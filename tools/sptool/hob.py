#!/usr/bin/python3
# Copyright (c) 2024, Arm Limited. All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

import struct

FFA_BOOT_INFO_HEADER_FMT_STR = "6IQ"
FFA_BOOT_INFO_DESC_FMT_STR = "H2BHIQ"
SIZEOF_BOOT_INFO_HEADER = struct.calcsize(FFA_BOOT_INFO_HEADER_FMT_STR)
SIZEOF_BOOT_INFO_DESC = struct.calcsize(FFA_BOOT_INFO_DESC_FMT_STR)

EFI_HOB_HANDOFF_TABLE_VERSION = 0x000a

PAGE_SIZE_SHIFT = 12 #TODO assuming 4K page size

# HobType values of EFI_HOB_GENERIC_HEADER.

EFI_HOB_TYPE_HANDOFF = 0x0001
EFI_HOB_TYPE_MEMORY_ALLOCATION = 0x0002
EFI_HOB_TYPE_RESOURCE_DESCRIPTOR = 0x0003
EFI_HOB_TYPE_GUID_EXTENSION = 0x0004
EFI_HOB_TYPE_FV = 0x0005
EFI_HOB_TYPE_CPU = 0x0006
EFI_HOB_TYPE_MEMORY_POOL = 0x0007
EFI_HOB_TYPE_FV2 = 0x0009
EFI_HOB_TYPE_LOAD_PEIM_UNUSED = 0x000A
EFI_HOB_TYPE_UEFI_CAPSULE = 0x000B
EFI_HOB_TYPE_FV3 = 0x000C
EFI_HOB_TYPE_UNUSED = 0xFFFE
EFI_HOB_TYPE_END_OF_HOB_LIST = 0xFFFF

# GUID values
'''struct efi_guid {
         uint32_t time_low;
         uint16_t time_mid;
         uint16_t time_hi_and_version;
         uint8_t clock_seq_and_node[8];
}'''

MM_PEI_MMRAM_MEMORY_RESERVE_GUID = (0x0703f912, 0xbf8d, 0x4e2a, (0xbe,
    0x07, 0xab, 0x27, 0x25, 0x25, 0xc5, 0x92 ))
MM_NS_BUFFER_GUID = (0xf00497e3, 0xbfa2, 0x41a1, (0x9d, 0x29, 0x54, 0xc2, 0xe9, 0x37,
     0x21, 0xc5 ))
MM_COMM_BUFFER_GUID = (0x6c2a2520, 0x0131, 0x4aee, (0xa7, 0x50, 0xcc, 0x38, 0x4a, 0xac, 0xe8, 0xc6))

# MMRAM states and capabilities
# See UEFI Platform Initialization Specification Version 1.8, IV-5.3.5
EFI_MMRAM_OPEN = 0x00000001
EFI_MMRAM_CLOSED = 0x00000002
EFI_MMRAM_LOCKED = 0x00000004
EFI_CACHEABLE = 0x00000008
EFI_ALLOCATED = 0x00000010
EFI_NEEDS_TESTING = 0x00000020
EFI_NEEDS_ECC_INITIALIZATION = 0x00000040

EFI_SMRAM_OPEN  = EFI_MMRAM_OPEN
EFI_SMRAM_CLOSED = EFI_MMRAM_CLOSED
EFI_SMRAM_LOCKED = EFI_MMRAM_LOCKED

# EFI boot mode.
EFI_BOOT_WITH_FULL_CONFIGURATION = 0x00
EFI_BOOT_WITH_MINIMAL_CONFIGURATION = 0x01
EFI_BOOT_ASSUMING_NO_CONFIGURATION_CHANGES = 0x02
EFI_BOOT_WITH_FULL_CONFIGURATION_PLUS_DIAGNOSTICS = 0x03
EFI_BOOT_WITH_DEFAULT_SETTINGS = 0x04
EFI_BOOT_ON_S4_RESUME = 0x05
EFI_BOOT_ON_S5_RESUME = 0x06
EFI_BOOT_WITH_MFG_MODE_SETTINGS = 0x07
EFI_BOOT_ON_S2_RESUME = 0x10
EFI_BOOT_ON_S3_RESUME = 0x11
EFI_BOOT_ON_FLASH_UPDATE = 0x12
EFI_BOOT_IN_RECOVERY_MODE = 0x20

STMM_BOOT_MODE = EFI_BOOT_WITH_FULL_CONFIGURATION
STMM_MMRAM_REGION_STATE_DEFAULT = EFI_CACHEABLE | EFI_ALLOCATED
STMM_MMRAM_REGION_STATE_HEAP = EFI_CACHEABLE

#helper for fdt nose property parsing
def get_uint32_property_value(fdt_node, name):
    if fdt_node.exist_property(name):
        property = fdt_node.get_property(name)
        if len(property) <= 1:
            return property.value
        if len(property) >1:
            value = 0
            shift = 0
            for word in reversed(property):
                value |= word << shift
                shift += 32
            return value
    else:
        return None

class HobList:
    def __init__(self, format_str, hob_list):
        self.format_str = format_str
        self.hob_list = hob_list

    def add(self, hob):
        if hob is not None:
            self.format_str += hob.format_str
            self.hob_list.append(hob)

    def get_list(self):
        return self.hob_list

    def get_phit(self):
        if self.hob_list is not None:
            if type(self.hob_list[0]) is not Handoff_Info_Table:
                raise Exception("First hob in list must be of type PHIT")
            return self.hob_list[0]

class EFI_GUID:
    def __init__(self, time_low, time_mid, time_hi_and_version,
            clock_seq_and_node):
        self.time_low = time_low
        self.time_mid = time_mid
        self.time_hi_and_version = time_hi_and_version
        self.clock_seq_and_node = clock_seq_and_node
        self.format_str = "IHH8B"

    def pack(self):
        return struct.pack(self.format_str, self.time_low, self.time_mid,
                self.time_hi_and_version, *self.clock_seq_and_node)

class Hob_Generic_Header:
    def __init__(self, hob_type, hob_length):
        self.format_str = "HHI"
        self.hob_type = hob_type
        self.hob_length = struct.calcsize(self.format_str) + hob_length
        self.reserved = 0

    def pack(self):
        return struct.pack(self.format_str, self.hob_type, self.hob_length, self.reserved)

class Hob_Guid:
    def __init__(self, name : EFI_GUID, data_format_str, data):

        hob_length = struct.calcsize(name.format_str) + \
            struct.calcsize(data_format_str)
        self.header = Hob_Generic_Header(EFI_HOB_TYPE_GUID_EXTENSION,
                hob_length)
        self.name = name
        self.data = data
        self.data_format_str = data_format_str
        self.format_str = self.header.format_str + self.name.format_str + data_format_str

    def pack(self):
        return self.header.pack() + self.name.pack() + struct.pack(self.data_format_str, *self.data)

class Handoff_Info_Table:
    def __init__(self, memory_base, memory_size, free_memory_base,
            free_memory_size):
        #TODO determine where values other than EFI defines come from
        #header,uint32t,uint32t, uint64_t * 5
        if memory_size is None:
            memory_size = 0
        if memory_base is None:
            memory_base = 0
        if free_memory_size is None:
            free_memory_size = 0

        self.format_str = "II5Q"
        hob_length = struct.calcsize(self.format_str) #TODO check
        self.header = Hob_Generic_Header(EFI_HOB_TYPE_HANDOFF, hob_length)
        self.version = EFI_HOB_HANDOFF_TABLE_VERSION
        self.boot_mode = STMM_BOOT_MODE #TODO make configurable if not stmm
        self.memory_top = memory_base + memory_size
        self.memory_bottom = memory_base
        self.free_memory_top = free_memory_base
        self.free_memory_bottom = free_memory_base + free_memory_size
        self.hob_end = None

    def set_hob_end_addr(self, hob_end_addr):
        self.hob_end = hob_end_addr

    def pack(self):
        return self.header.pack() + struct.pack(self.format_str, self.version,
                self.boot_mode, self.memory_top, self.memory_bottom,
                self.free_memory_top, self.free_memory_bottom, self.hob_end)

class Firmware_Volume_Hob:
    def __init__(self, base_address, page_count, granule):
        #header, uint64_t, uint64_t
        self.data_format_str = "2Q"
        hob_length = struct.calcsize(self.data_format_str)
        self.header = Hob_Generic_Header(EFI_HOB_TYPE_FV, hob_length)
        self.format_str = self.header.format_str + self.data_format_str
        self.base_address = base_address
        self.length = page_count

    def pack(self):
        return self.header.pack() + struct.pack(self.data_format_str,
                self.base_address, self.length)

class End_of_Hoblist_Hob:
    def __init__(self):
        self.header = Hob_Generic_Header(EFI_HOB_TYPE_END_OF_HOB_LIST, 0)
        self.format_str = ""

    def pack(self):
        return self.header.pack()

def generate_mmram_desc(base_addr, page_count, granule, region_state):
    physical_size = page_count << PAGE_SIZE_SHIFT
    physical_start = base_addr
    cpu_start = base_addr

    return ("4Q", (physical_start, cpu_start, physical_size, \
        region_state))

def generate_ns_buffer_guid(mmram_desc):
    return Hob_Guid(EFI_GUID(*MM_NS_BUFFER_GUID), *mmram_desc)

def generate_shared_buf_guid(mmram_desc):
    return Hob_Guid(EFI_GUID(*MM_COMM_BUFFER_GUID), *mmram_desc)

def generate_pei_mmram_memory_reserve_guid(regions):
    #uint32t n_reserved regions, array of mmram descriptors
    format_str = "I"
    data = [len(regions)]
    for desc_format_str, mmram_desc in regions:
        format_str += desc_format_str
        data.extend(mmram_desc)
    guid_data = (format_str, data)
    return Hob_Guid(EFI_GUID(*MM_PEI_MMRAM_MEMORY_RESERVE_GUID), *guid_data)

def generate_hob_from_fdt_node(sp_fdt):
    fv_hob = None
    ns_buffer_hob = None
    mmram_reserve_hob = None
    shared_buf_hob = None

    load_address = get_uint32_property_value(sp_fdt, 'load-address')
    entry_point_offset = get_uint32_property_value(sp_fdt, 'entrypoint-offset')
    img_size = get_uint32_property_value(sp_fdt, 'image-size')
#   TODO:  boot_info_size = get_pm_offset(sp_node)
    boot_info_size = 0
    max_table_size = boot_info_size - (SIZEOF_BOOT_INFO_HEADER + SIZEOF_BOOT_INFO_DESC)
    free_memory_base = load_address + (SIZEOF_BOOT_INFO_HEADER +
            SIZEOF_BOOT_INFO_DESC)

    if sp_fdt.exist_node('memory-regions'):
        if sp_fdt.exist_property('xlat-granule'):
            granule = int(sp_fdt.get_property('xlat-granule').value)
        else:
            # Default granule to 4K
            granule = 0
        memory_regions = sp_fdt.get_node('memory-regions')
        regions = []

        # OD: reserve FV image memory as first entry
        regions.append(generate_mmram_desc(0x7003000, 0x300-3, 0, STMM_MMRAM_REGION_STATE_DEFAULT))

        for node in memory_regions.nodes:
            base_addr = get_uint32_property_value(node, 'base-address')
            #offset = get_uint32_property_value(node, 'load-address-relative-offset')
            page_count = get_uint32_property_value(node, 'pages-count')

            #if node.name.strip() == "stmm_region":
                #fv_hob = Firmware_Volume_Hob(0x0, page_count, granule)
                #check_stmm_fv_hob(fv_hob, load_address, img_size)
                #img_size = fv_hob.length

            region_state = STMM_MMRAM_REGION_STATE_DEFAULT
            if node.name.strip() == "heap":
                region_state = STMM_MMRAM_REGION_STATE_HEAP

            mmram_desc = generate_mmram_desc(base_addr, page_count, granule, region_state)

            if node.name.strip() == "ns_comm_buffer":
                ns_buffer_hob = generate_ns_buffer_guid(mmram_desc)

            if node.name.strip() == "rx-tx-buffers":
                shared_buf_desc = ("2Q", (base_addr, page_count))
                shared_buf_hob = generate_shared_buf_guid(shared_buf_desc)

            regions.append(mmram_desc)

        mmram_reserve_hob = generate_pei_mmram_memory_reserve_guid(regions)

    img_start = load_address + entry_point_offset
    fv_hob = Firmware_Volume_Hob(img_start, img_size - 3*4096, 0)

    #TODO remove
    if img_size is None:
        img_size = 0

    phit = Handoff_Info_Table(img_start, img_size, free_memory_base, max_table_size)
    end_hob = End_of_Hoblist_Hob()
    hob_list = HobList("", [])

    # Write to hob binary
    if phit is not None:
        hob_list.add(phit)
    if fv_hob is not None:
        hob_list.add(fv_hob)
    if ns_buffer_hob is not None:
        hob_list.add(ns_buffer_hob)
    if mmram_reserve_hob is not None:
        hob_list.add(mmram_reserve_hob)
    if shared_buf_hob is not None:
        hob_list.add(shared_buf_hob)
    if end_hob is not None:
        hob_list.add(end_hob)

    #TODO check this
    hob_list.get_phit().set_hob_end_addr(free_memory_base +
            struct.calcsize(hob_list.format_str))

    return hob_list
