Building and running StandaloneMM as a S-EL0 secure partition
=============================================================

This document explains how to build and run the EDKII/StandaloneMM component as a S-EL0 secure partition on top of Hafnium (S-EL2 secure partition manager) on the FVP platform.

This isn't an integration document and instructions are provided for demonstration purpose.

Assuming the build is done on a x86 host, we use gcc 14.2 for cross compiling EDKII and TF-A:

    mkdir workspace; cd workspace
    wget https://developer.arm.com/-/media/Files/downloads/gnu/14.2.rel1/binrel/arm-gnu-toolchain-14.2.rel1-x86_64-aarch64-none-elf.tar.xz
    xz -d arm-gnu-toolchain-14.2.rel1-x86_64-aarch64-none-elf.tar.xz
    tar xvf arm-gnu-toolchain-14.2.rel1-x86_64-aarch64-none-elf.tar
    rm xvf arm-gnu-toolchain-14.2.rel1-x86_64-aarch64-none-elf.tar
    PATH=$PWD/arm-gnu-toolchain-14.2.rel1-x86_64-aarch64-none-elf/bin:$PATH

Hafnium
-------

    git clone --recurse-submodules https://github.com/odeprez/hafnium.git
    cd hafnium/project/reference
    git remote add github https://github.com/odeprez/hafnium-project-reference.git
    git fetch github
    git checkout github/topics/od/hf_stmm_fvp_upstream
    cd ../..
    git checkout topics/od/hf_stmm_fvp_upstream

Install pre-requisites (https://hafnium.readthedocs.io/en/latest/getting_started/prerequisites.html) and build preferably through docker:

    export HAFNIUM_HERMETIC_BUILD=true
    make
    cd ..

EDKII
-----

Clone in workspace directory from above and setup:

    git clone git@github.com:odeprez/edk2.git -b topics/od/hf_stmm_fvp_upstream
    git clone git@github.com:odeprez/edk2-platforms.git -b topics/od/hf_stmm_fvp_upstream
    git clone https://github.com/tianocore/edk2-non-osi.git

    export WORKSPACE=`pwd`
    export PACKAGES_PATH=$PWD/edk2:$PWD/edk2-platforms:$PWD/edk2-non-osi
    export NUM_CPUS=$((`getconf _NPROCESSORS_ONLN` + 2))

    cd edk2
    git submodule update --init
    . ./edksetup.sh
    cd ..

    make -j8 -C edk2/BaseTools/Source/C

Then build with:

    GCC5_AARCH64_PREFIX=aarch64-none-elf- build -n $NUM_CPUS -a AARCH64 -t GCC5 -p Platform/ARM/VExpressPkg/PlatformStandaloneMm.dsc
    GCC5_AARCH64_PREFIX=aarch64-none-elf- build -n $NUM_CPUS -a AARCH64 -t GCC5 -p Platform/ARM/VExpressPkg/ArmVExpress-FVP-AArch64.dsc

TF-A
----

Install pre-requisites from https://trustedfirmware-a.readthedocs.io/en/latest/getting_started/prerequisites.html

In particular make sure you have poetry installed as it's necessary for building secure partition packages.

Clone in workspace directory and build:

    git clone https://github.com/odeprez/arm-trusted-firmware.git trusted-firmware-a -b topics/od/hf_stmm_fvp_upstream; cd trusted-firmware-a

    make -j8 CROSS_COMPILE=aarch64-none-elf- PLAT=fvp DEBUG=1 SPD=spmd BRANCH_PROTECTION=1 ENABLE_FEAT_MTE2=1 ARM_ARCH_MAJOR=8 ARM_ARCH_MINOR=5 BL33=../Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/FV/FVMAIN_COMPACT.Fv BL32=../hafnium/out/reference/secure_aem_v8a_fvp_vhe_clang/hafnium.bin SP_LAYOUT_FILE=sp_layout.json ARM_SPMC_MANIFEST_DTS=plat/arm/board/fvp/fdts/fvp_spmc_stmm_sp_manifest.dts ARM_BL2_SP_LIST_DTS=fvp_fw_config_fragment.dts all fip

    cd  ..

Get and run the FVP model
-------------------------

Get the model from https://developer.arm.com/Tools%20and%20Software/Fixed%20Virtual%20Platforms/Arm%20Architecture%20FVPs:

    wget https://developer.arm.com/-/cdn-downloads/permalink/FVPs-Architecture/FM-11.29/FVP_Base_RevC-2xAEMvA_11.29_27_Linux64.tgz
    tar xvfz FVP_Base_RevC-2xAEMvA_11.29_27_Linux64.tgz
    rm FVP_Base_RevC-2xAEMvA_11.29_27_Linux64.tgz

Then run:

    Base_RevC_AEMvA_pkg/models/Linux64_GCC-9.3/FVP_Base_RevC-2xAEMvA -C pctl.startup=0.0.0.0 -C cluster0.NUM_CORES=4 -C cluster1.NUM_CORES=4 -C bp.secure_memory=1 -C bp.secureflashloader.fname=trusted-firmware-a/build/fvp/debug/bl1.bin -C bp.flashloader0.fname=trusted-firmware-a/build/fvp/debug/fip.bin -C bp.pl011_uart0.out_file=fvp-uart0.log -C bp.pl011_uart1.out_file=fvp-uart1.log -C bp.pl011_uart2.out_file=fvp-uart2.log -C cluster0.has_arm_v8-5=1 -C cluster1.has_arm_v8-5=1 -C cluster0.has_branch_target_exception=1 -C cluster1.has_branch_target_exception=1 -C cluster0.has_pointer_authentication=2 -C cluster1.has_pointer_authentication=2 -C pci.pci_smmuv3.mmu.SMMU_AIDR=2 -C pci.pci_smmuv3.mmu.SMMU_IDR0=0x0046123B -C pci.pci_smmuv3.mmu.SMMU_IDR1=0x00600002 -C pci.pci_smmuv3.mmu.SMMU_IDR3=0x1714 -C pci.pci_smmuv3.mmu.SMMU_IDR5=0xFFFF0472 -C pci.pci_smmuv3.mmu.SMMU_S_IDR1=0xA0000002 -C pci.pci_smmuv3.mmu.SMMU_S_IDR2=0 -C pci.pci_smmuv3.mmu.SMMU_S_IDR3=0 -C cluster0.memory_tagging_support_level=2 -C cluster1.memory_tagging_support_level=2 -C bp.dram_metadata.is_enabled=1 -C gic_distributor.ARE-fixed-to-one=1 -C cluster0.gicv3.extended-interrupt-range-support=1 -C cluster1.gicv3.extended-interrupt-range-support=1 -C gic_distributor.extended-ppi-count=64 -C gic_distributor.extended-spi-count=1024


It boots TF-A, Hafnium, StandaloneMM and then reaches the UEFI boot menu in the normal world.

Logs
----

Logs are stored after simulation in fvp-uart0.log and fvp-uart1.log

fvp-uart0.log
-------------

```
NOTICE:  Booting Trusted Firmware
NOTICE:  BL1: v2.13.0(debug):1821ccd01-dirty
NOTICE:  BL1: Built : 09:39:27, Jul  1 2025
INFO:    BL1: RAM 0x4033000 - 0x403a000
INFO:    Loading image id=32 at address 0x4001010
INFO:    Image id=32 loaded: 0x4001010 - 0x400125f
INFO:    FCONF: Config file with image ID:32 loaded at address = 0x4001010
INFO:    Loading image id=24 at address 0x4001300
INFO:    Image id=24 loaded: 0x4001300 - 0x4001494
INFO:    FCONF: Config file with image ID:24 loaded at address = 0x4001300
INFO:    BL1: Loading BL2
INFO:    Loading image id=1 at address 0x401f000
INFO:    Image id=1 loaded: 0x401f000 - 0x4028c01
NOTICE:  BL1: Booting BL2
INFO:    Entry point address = 0x401f000
INFO:    SPSR = 0x3c5
INFO:    FCONF: Reading FW_CONFIG firmware configuration file from: 0x4001010
INFO:    FCONF: Reading firmware configuration information for: dyn_cfg
INFO:    FCONF: Reading TB_FW firmware configuration file from: 0x4001300
INFO:    FCONF: Reading firmware configuration information for: arm_sp
NOTICE:  BL2: v2.13.0(debug):1821ccd01-dirty
NOTICE:  BL2: Built : 09:39:27, Jul  1 2025
INFO:    BL2: Doing platform setup
INFO:    Configuring TrustZone Controller
INFO:    Total 8 regions set.
INFO:    BL2: Loading image id 3
INFO:    Loading image id=3 at address 0x4003000
INFO:    Image id=3 loaded: 0x4003000 - 0x401b1e5
INFO:    BL2: Loading image id 23
INFO:    Loading image id=23 at address 0x7f00000
INFO:    Image id=23 loaded: 0x7f00000 - 0x7f02a9c
INFO:    BL2: Loading image id 25
INFO:    Loading image id=25 at address 0x4001300
INFO:    Image id=25 loaded: 0x4001300 - 0x4001348
INFO:    BL2: Loading image id 4
INFO:    Loading image id=4 at address 0x6000000
INFO:    Image id=4 loaded: 0x6000000 - 0x6030320
INFO:    BL2: Skip loading image id 21
INFO:    BL2: Skip loading image id 22
INFO:    BL2: Loading image id 26
INFO:    Loading image id=26 at address 0x4001500
INFO:    Image id=26 loaded: 0x4001500 - 0x4001a81
INFO:    BL2: Loading image id 5
INFO:    Loading image id=5 at address 0x88000000
INFO:    Image id=5 loaded: 0x88000000 - 0x88280000
INFO:    BL2: Loading image id 27
INFO:    Loading image id=27 at address 0x80000000
INFO:    Image id=27 loaded: 0x80000000 - 0x80000048
INFO:    BL2: Loading image id 41
INFO:    Loading image id=41 at address 0x7000000
INFO:    Image id=41 loaded: 0x7000000 - 0x7103000
NOTICE:  BL1: Booting BL31
INFO:    Entry point address = 0x4003000
INFO:    SPSR = 0x3cd
INFO:    BL31 FCONF: FW_CONFIG address = 4001010
INFO:    FCONF: Reading FW_CONFIG firmware configuration file from: 0x4001010
INFO:    FCONF: Reading firmware configuration information for: dyn_cfg
INFO:    FCONF: Reading HW_CONFIG firmware configuration file from: 0x7f00000
INFO:    FCONF: Reading firmware configuration information for: gicv3_config
INFO:    FCONF: Reading firmware configuration information for: pci_props
WARNING: FCONF: Unable to locate 'pci' node
INFO:    FCONF: Reading firmware configuration information for: dram_layout
INFO:    FCONF: Reading firmware configuration information for: cpu_timer
INFO:    FCONF: Reading firmware configuration information for: uart_config
INFO:    FCONF: Reading firmware configuration information for: topology
NOTICE:  BL31: v2.13.0(debug):1821ccd01-dirty
NOTICE:  BL31: Built : 09:39:28, Jul  1 2025
INFO:    GICv3 without legacy support detected.
INFO:    ARM GICv3 driver initialized in EL3
INFO:    Maximum SPI INTID supported: 255
INFO:    BL31: Initializing runtime services
INFO:    SPM Core setup done.
INFO:    BL31: Initializing BL32
INFO: Initializing Hafnium (SPMC)
INFO: text: 0x6000000 - 0x6028000
INFO: rodata: 0x6028000 - 0x6030000
INFO: data: 0x6030000 - 0x6113000
INFO: stacks: 0x6120000 - 0x6130000
INFO: Supported bits in physical address: 40
INFO: Stage 2 has 4 page table levels with 2 pages at the root.
INFO: Stage 1 has 5 page table levels with 1 pages at the root.
INFO: Memory range:  0x6000000 - 0x7ffffff
INFO: Arm SMMUv3 initialized
INFO: Unable to find '/interrupt-controller. Using default configuration.'
INFO: Loading VM id 0x8001: stmm.
INFO: Loaded with 1 vCPUs, entry at 0x7000000.
INFO: Hafnium initialisation completed
[8001 0] FF-A Version: Major=0x1, Minor=0x2
[8001 0] Start Dump Hob: 7002000
[8001 0] FvHob: BaseAddress - 0x7003000
[8001 0] FvHob: Length - 3133440
[8001 0] MmramDescriptor[NsBuffer]: PhysicalStart - 0x80000000
[8001 0] MmramDescriptors[NsBuffer]: CpuStart - 0x80000000
[8001 0] MmramDescriptors[NsBuffer]: PhysicalSize - 65536
[8001 0] MmramDescriptors[NsBuffer]: RegionState - 0x18
[8001 0] MmramDescriptor[PeiMemReserved]: PhysicalStart - 0x7000000
[8001 0] MmramDescriptors[PeiMemReserved]: CpuStart - 0x7000000
[8001 0] MmramDescriptors[PeiMemReserved]: PhysicalSize - 3145728
[8001 0] MmramDescriptors[PeiMemReserved]: RegionState - 0x18
[8001 0] MmramDescriptor[PeiMemReserved]: PhysicalStart - 0x7600000
[8001 0] MmramDescriptors[PeiMemReserved]: CpuStart - 0x7600000
[8001 0] MmramDescriptors[PeiMemReserved]: PhysicalSize - 65536
[8001 0] MmramDescriptors[PeiMemReserved]: RegionState - 0x18
[8001 0] MmramDescriptor[PeiMemReserved]: PhysicalStart - 0x7700000
[8001 0] MmramDescriptors[PeiMemReserved]: CpuStart - 0x7700000
[8001 0] MmramDescriptors[PeiMemReserved]: PhysicalSize - 4194304
[8001 0] MmramDescriptors[PeiMemReserved]: RegionState - 0x8
[8001 0] MmramDescriptor[PeiMemReserved]: PhysicalStart - 0x80000000
[8001 0] MmramDescriptors[PeiMemReserved]: CpuStart - 0x80000000
[8001 0] MmramDescriptors[PeiMemReserved]: PhysicalSize - 65536
[8001 0] MmramDescriptors[PeiMemReserved]: RegionState - 0x18
[8001 0] End Dump Hob: 7002000
[8001 0] Found Standalone MM PE data - 0x7004000
[8001 0] Found Standalone MM PE data - 0x7004000
[8001 0] Standalone MM Core PE-COFF SectionHeaderOffset - 0xF60, NumberOfSections - 3
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 0 of image at 0x7004000 has 0x60000020 permissions
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 0 of image at 0x7004000 has .text name
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 0 of image at 0x7004000 has 0x7005000 address
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 0 of image at 0x7004000 has 0x1000 data
[8001 0] UpdateMmFoundationPeCoffPermissions: Ignoring section 0 of image at 0x7004000 with 0x60000020 permissions
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 1 of image at 0x7004000 has 0xC0000040 permissions
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 1 of image at 0x7004000 has .data name
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 1 of image at 0x7004000 has 0x7015000 address
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 1 of image at 0x7004000 has 0x11000 data
[8001 0] UpdateMmFoundationPeCoffPermissions: Mapping section 1 of image at 0x7004000 with RW-XN permissions
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 2 of image at 0x7004000 has 0x42000040 permissions
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 2 of image at 0x7004000 has .reloc name
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 2 of image at 0x7004000 has 0x7019000 address
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 2 of image at 0x7004000 has 0x15000 data
[8001 0] UpdateMmFoundationPeCoffPermissions: Mapping section 2 of image at 0x7004000 with RO-XN permissions
[8001 0] MmMain - 0x7002000
[8001 0] MmramRangeCount - 0x4
[8001 0] MmramRanges[0]: 0x0000000007000000 - 0x300000
[8001 0] MmramRanges[1]: 0x0000000007600000 - 0x10000
[8001 0] MmramRanges[2]: 0x0000000007700000 - 0x400000
[8001 0] MmramRanges[3]: 0x0000000080000000 - 0x10000
[8001 0] MmInitializeMemoryServices
[8001 0] MmAddMemoryRegion 2 : 0x0000000007700000 - 0x0000000000400000
[8001 0] HobSize - 0x130
[8001 0] MmHobStart - 0x7AEFE10
[8001 0] MmInstallConfigurationTable For HobList
[8001 0] mMmMemLibInternalMaximumSupportAddress = 0xFFFFFFFFFFFF
[8001 0] Print all Hob information from Hob 0x7AEFE10
[8001 0] HOB[0]: Type = EFI_HOB_TYPE_HANDOFF, Offset = 0x0, Length = 0x38
[8001 0]    BootMode            = 0x0
[8001 0]    EfiMemoryTop        = 0x7303000
[8001 0]    EfiMemoryBottom     = 0x7000000
[8001 0]    EfiFreeMemoryTop    = 0x7003000
[8001 0]    EfiFreeMemoryBottom = 0x7002130
[8001 0]    EfiEndOfHobList     = 0x7002128
[8001 0] HOB[1]: Type = EFI_HOB_TYPE_FV, Offset = 0x38, Length = 0x18
[8001 0]    BaseAddress = 0x7003000
[8001 0]    Length      = 0x2FD000
[8001 0] HOB[2]: Type = EFI_HOB_TYPE_GUID_EXTENSION, Offset = 0x50, Length = 0x38
[8001 0]    Name       = F00497E3-BFA2-41A1-9D29-54C2E93721C5
[8001 0]    DataLength = 0x20
[8001 0] HOB[3]: Type = EFI_HOB_TYPE_GUID_EXTENSION, Offset = 0x88, Length = 0xA0
[8001 0]    Name       = 0703F912-BF8D-4E2A-BE07-AB272525C592
[8001 0]    DataLength = 0x88
[8001 0] There are totally 4 Hobs, the End Hob address is 7AEFF38
[8001 0] MmRegisterProtocolNotify - MmConfigurationMmProtocol
[8001 0] MmDispatchFvs: FV[0] address = 0x7003000, size = 0x2FD000
[8001 0] MmCoreFfsFindMmDriver - 0x7003000
[8001 0] FvIsBeingProcessed - 0x07003000
[8001 0] Processing compressed firmware volume (AuthenticationStatus == 0)
[8001 0] MmCoreFfsFindMmDriver - 0x7AD9010
[8001 0] FvIsBeingProcessed - 0x07AD9010
[8001 0] Check MmFileTypes - 0xE
[8001 0] Find PE data - 0x7AD90AC
[8001 0] MmAddToDriverList - 58F7A62B-6280-42A7-BC38-10535A64A92C (0x07AD90AC)
[8001 0] Check MmFileTypes - 0xE
[8001 0] MmDispatcher
[8001 0]   Drain the Scheduled Queue
[8001 0]   Search DriverList for items to place on Scheduled Queue
[8001 0]   DriverEntry (Discovered) - 58F7A62B-6280-42A7-BC38-10535A64A92C
[8001 0] Evaluate MM DEPEX for FFS(58F7A62B-6280-42A7-BC38-10535A64A92C)
[8001 0]   TRUE
[8001 0]   END
[8001 0]   RESULT = TRUE
[8001 0]   Drain the Scheduled Queue
[8001 0]   DriverEntry (Scheduled) - 58F7A62B-6280-42A7-BC38-10535A64A92C
[8001 0] MmLoadImage - 58F7A62B-6280-42A7-BC38-10535A64A92C
[8001 0] UpdatePeCoffPermissions: Mapping section 0 of image at 0x7AE8000 with RO-X permissions and size 0x2000
[8001 0] UpdatePeCoffPermissions: Mapping section 1 of image at 0x7AEA000 with RW-XN permissions and size 0x1000
[8001 0] UpdatePeCoffPermissions: Mapping section 2 of image at 0x7AEB000 with RO-XN permissions and size 0x1000
[8001 0] MmInstallProtocolInterface: 5B1B31A1-9562-11D2-8E3F-00A0C969723B 7AEF890
[8001 0] Loading MM driver at 0x00007AE7000 EntryPoint=0x00007AE95A8 StandaloneMmCpu.efi
[8001 0] StartImage - 0x7AE95A8 (Standalone Mode)
[8001 0] MmInstallProtocolInterface: 26EEB3DE-B689-492E-80F0-BE8BD7DA4BA7 7AEA028
[8001 0] MmConfigurationMmNotify(26EEB3DE-B689-492E-80F0-BE8BD7DA4BA7) - 7AEA028
[8001 0] MM Core registered MM Entry Point address 7008A74
[8001 0] MmInstallProtocolInterface: 6ECBD5A1-C0F8-4702-8301-4FC2C5470A51 7AEA010
[8001 0]   Search DriverList for items to place on Scheduled Queue
[8001 0]   DriverEntry (Discovered) - 58F7A62B-6280-42A7-BC38-10535A64A92C
[8001 0]   no more MM driver to dispatch, stop the dispatch request
[8001 0]   DriverEntry (Discovered) - 58F7A62B-6280-42A7-BC38-10535A64A92C
[8001 0] MmiHandlerRegister - GUID 7E6EFFFA-69B4-4C1B-A4C7-AFF9C9244FEE - Status 0
[8001 0] MmiHandlerRegister - GUID 60FF8964-E906-41D0-AFED-F241E974E08E - Status 0
[8001 0] MmiHandlerRegister - GUID F33E1BF3-980B-4BFB-A29A-B29C86453732 - Status 0
[8001 0] MmiHandlerRegister - GUID 02CE967A-DD7E-4FFC-9EE7-810CF0470880 - Status 0
[8001 0] MmiHandlerRegister - GUID 27ABF055-B1B8-4C26-8048-748F37BAA2DF - Status 0
[8001 0] MmiHandlerRegister - GUID 7CE88FB3-4BD7-4679-87A8-A8D8DEE50D2B - Status 0
[8001 0] Failed to find MM Communication Buffer HOB
[8001 0] Only Root MMI Handlers will be supported!
[8001 0] MmMain Done!
[8001 0] Shared Cpu Driver EP 7AE940C
NOTICE: Finished bootstrapping all SPs on CPU0
INFO:    BL31: Preparing for EL3 exit to normal world
INFO:    Entry point address = 0x88000000
INFO:    SPSR = 0x3c9
[2J[04D[=3h[2J[09DPress ESCAPE for boot options ...........NOTICE:  Booting Trusted Firmware
NOTICE:  BL1: v2.13.0(debug):1821ccd01-dirty
NOTICE:  BL1: Built : 09:39:27, Jul  1 2025
INFO:    BL1: RAM 0x4033000 - 0x403a000
INFO:    Loading image id=32 at address 0x4001010
INFO:    Image id=32 loaded: 0x4001010 - 0x400125f
INFO:    FCONF: Config file with image ID:32 loaded at address = 0x4001010
INFO:    Loading image id=24 at address 0x4001300
INFO:    Image id=24 loaded: 0x4001300 - 0x4001494
INFO:    FCONF: Config file with image ID:24 loaded at address = 0x4001300
INFO:    BL1: Loading BL2
INFO:    Loading image id=1 at address 0x401f000
INFO:    Image id=1 loaded: 0x401f000 - 0x4028c01
NOTICE:  BL1: Booting BL2
INFO:    Entry point address = 0x401f000
INFO:    SPSR = 0x3c5
INFO:    FCONF: Reading FW_CONFIG firmware configuration file from: 0x4001010
INFO:    FCONF: Reading firmware configuration information for: dyn_cfg
INFO:    FCONF: Reading TB_FW firmware configuration file from: 0x4001300
INFO:    FCONF: Reading firmware configuration information for: arm_sp
NOTICE:  BL2: v2.13.0(debug):1821ccd01-dirty
NOTICE:  BL2: Built : 09:39:27, Jul  1 2025
INFO:    BL2: Doing platform setup
INFO:    Configuring TrustZone Controller
INFO:    Total 8 regions set.
INFO:    BL2: Loading image id 3
INFO:    Loading image id=3 at address 0x4003000
INFO:    Image id=3 loaded: 0x4003000 - 0x401b1e5
INFO:    BL2: Loading image id 23
INFO:    Loading image id=23 at address 0x7f00000
INFO:    Image id=23 loaded: 0x7f00000 - 0x7f02a9c
INFO:    BL2: Loading image id 25
INFO:    Loading image id=25 at address 0x4001300
INFO:    Image id=25 loaded: 0x4001300 - 0x4001348
INFO:    BL2: Loading image id 4
INFO:    Loading image id=4 at address 0x6000000
INFO:    Image id=4 loaded: 0x6000000 - 0x6030320
INFO:    BL2: Skip loading image id 21
INFO:    BL2: Skip loading image id 22
INFO:    BL2: Loading image id 26
INFO:    Loading image id=26 at address 0x4001500
INFO:    Image id=26 loaded: 0x4001500 - 0x4001a81
INFO:    BL2: Loading image id 5
INFO:    Loading image id=5 at address 0x88000000
INFO:    Image id=5 loaded: 0x88000000 - 0x88280000
INFO:    BL2: Loading image id 27
INFO:    Loading image id=27 at address 0x80000000
INFO:    Image id=27 loaded: 0x80000000 - 0x80000048
INFO:    BL2: Loading image id 41
INFO:    Loading image id=41 at address 0x7000000
INFO:    Image id=41 loaded: 0x7000000 - 0x7103000
NOTICE:  BL1: Booting BL31
INFO:    Entry point address = 0x4003000
INFO:    SPSR = 0x3cd
INFO:    BL31 FCONF: FW_CONFIG address = 4001010
INFO:    FCONF: Reading FW_CONFIG firmware configuration file from: 0x4001010
INFO:    FCONF: Reading firmware configuration information for: dyn_cfg
INFO:    FCONF: Reading HW_CONFIG firmware configuration file from: 0x7f00000
INFO:    FCONF: Reading firmware configuration information for: gicv3_config
INFO:    FCONF: Reading firmware configuration information for: pci_props
WARNING: FCONF: Unable to locate 'pci' node
INFO:    FCONF: Reading firmware configuration information for: dram_layout
INFO:    FCONF: Reading firmware configuration information for: cpu_timer
INFO:    FCONF: Reading firmware configuration information for: uart_config
INFO:    FCONF: Reading firmware configuration information for: topology
NOTICE:  BL31: v2.13.0(debug):1821ccd01-dirty
NOTICE:  BL31: Built : 09:39:28, Jul  1 2025
INFO:    GICv3 without legacy support detected.
INFO:    ARM GICv3 driver initialized in EL3
INFO:    Maximum SPI INTID supported: 255
INFO:    BL31: Initializing runtime services
INFO:    SPM Core setup done.
INFO:    BL31: Initializing BL32
INFO: Initializing Hafnium (SPMC)
INFO: text: 0x6000000 - 0x6028000
INFO: rodata: 0x6028000 - 0x6030000
INFO: data: 0x6030000 - 0x6113000
INFO: stacks: 0x6120000 - 0x6130000
INFO: Supported bits in physical address: 40
INFO: Stage 2 has 4 page table levels with 2 pages at the root.
INFO: Stage 1 has 5 page table levels with 1 pages at the root.
INFO: Memory range:  0x6000000 - 0x7ffffff
INFO: Arm SMMUv3 initialized
INFO: Unable to find '/interrupt-controller. Using default configuration.'
INFO: Loading VM id 0x8001: stmm.
INFO: Loaded with 1 vCPUs, entry at 0x7000000.
INFO: Hafnium initialisation completed
[8001 0] FF-A Version: Major=0x1, Minor=0x2
[8001 0] Start Dump Hob: 7002000
[8001 0] FvHob: BaseAddress - 0x7003000
[8001 0] FvHob: Length - 3133440
[8001 0] MmramDescriptor[NsBuffer]: PhysicalStart - 0x80000000
[8001 0] MmramDescriptors[NsBuffer]: CpuStart - 0x80000000
[8001 0] MmramDescriptors[NsBuffer]: PhysicalSize - 65536
[8001 0] MmramDescriptors[NsBuffer]: RegionState - 0x18
[8001 0] MmramDescriptor[PeiMemReserved]: PhysicalStart - 0x7000000
[8001 0] MmramDescriptors[PeiMemReserved]: CpuStart - 0x7000000
[8001 0] MmramDescriptors[PeiMemReserved]: PhysicalSize - 3145728
[8001 0] MmramDescriptors[PeiMemReserved]: RegionState - 0x18
[8001 0] MmramDescriptor[PeiMemReserved]: PhysicalStart - 0x7600000
[8001 0] MmramDescriptors[PeiMemReserved]: CpuStart - 0x7600000
[8001 0] MmramDescriptors[PeiMemReserved]: PhysicalSize - 65536
[8001 0] MmramDescriptors[PeiMemReserved]: RegionState - 0x18
[8001 0] MmramDescriptor[PeiMemReserved]: PhysicalStart - 0x7700000
[8001 0] MmramDescriptors[PeiMemReserved]: CpuStart - 0x7700000
[8001 0] MmramDescriptors[PeiMemReserved]: PhysicalSize - 4194304
[8001 0] MmramDescriptors[PeiMemReserved]: RegionState - 0x8
[8001 0] MmramDescriptor[PeiMemReserved]: PhysicalStart - 0x80000000
[8001 0] MmramDescriptors[PeiMemReserved]: CpuStart - 0x80000000
[8001 0] MmramDescriptors[PeiMemReserved]: PhysicalSize - 65536
[8001 0] MmramDescriptors[PeiMemReserved]: RegionState - 0x18
[8001 0] End Dump Hob: 7002000
[8001 0] Found Standalone MM PE data - 0x7004000
[8001 0] Found Standalone MM PE data - 0x7004000
[8001 0] Standalone MM Core PE-COFF SectionHeaderOffset - 0xF60, NumberOfSections - 3
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 0 of image at 0x7004000 has 0x60000020 permissions
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 0 of image at 0x7004000 has .text name
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 0 of image at 0x7004000 has 0x7005000 address
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 0 of image at 0x7004000 has 0x1000 data
[8001 0] UpdateMmFoundationPeCoffPermissions: Ignoring section 0 of image at 0x7004000 with 0x60000020 permissions
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 1 of image at 0x7004000 has 0xC0000040 permissions
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 1 of image at 0x7004000 has .data name
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 1 of image at 0x7004000 has 0x7015000 address
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 1 of image at 0x7004000 has 0x11000 data
[8001 0] UpdateMmFoundationPeCoffPermissions: Mapping section 1 of image at 0x7004000 with RW-XN permissions
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 2 of image at 0x7004000 has 0x42000040 permissions
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 2 of image at 0x7004000 has .reloc name
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 2 of image at 0x7004000 has 0x7019000 address
[8001 0] UpdateMmFoundationPeCoffPermissions: Section 2 of image at 0x7004000 has 0x15000 data
[8001 0] UpdateMmFoundationPeCoffPermissions: Mapping section 2 of image at 0x7004000 with RO-XN permissions
[8001 0] MmMain - 0x7002000
[8001 0] MmramRangeCount - 0x4
[8001 0] MmramRanges[0]: 0x0000000007000000 - 0x300000
[8001 0] MmramRanges[1]: 0x0000000007600000 - 0x10000
[8001 0] MmramRanges[2]: 0x0000000007700000 - 0x400000
[8001 0] MmramRanges[3]: 0x0000000080000000 - 0x10000
[8001 0] MmInitializeMemoryServices
[8001 0] MmAddMemoryRegion 2 : 0x0000000007700000 - 0x0000000000400000
[8001 0] HobSize - 0x130
[8001 0] MmHobStart - 0x7AEFE10
[8001 0] MmInstallConfigurationTable For HobList
[8001 0] mMmMemLibInternalMaximumSupportAddress = 0xFFFFFFFFFFFF
[8001 0] Print all Hob information from Hob 0x7AEFE10
[8001 0] HOB[0]: Type = EFI_HOB_TYPE_HANDOFF, Offset = 0x0, Length = 0x38
[8001 0]    BootMode            = 0x0
[8001 0]    EfiMemoryTop        = 0x7303000
[8001 0]    EfiMemoryBottom     = 0x7000000
[8001 0]    EfiFreeMemoryTop    = 0x7003000
[8001 0]    EfiFreeMemoryBottom = 0x7002130
[8001 0]    EfiEndOfHobList     = 0x7002128
[8001 0] HOB[1]: Type = EFI_HOB_TYPE_FV, Offset = 0x38, Length = 0x18
[8001 0]    BaseAddress = 0x7003000
[8001 0]    Length      = 0x2FD000
[8001 0] HOB[2]: Type = EFI_HOB_TYPE_GUID_EXTENSION, Offset = 0x50, Length = 0x38
[8001 0]    Name       = F00497E3-BFA2-41A1-9D29-54C2E93721C5
[8001 0]    DataLength = 0x20
[8001 0] HOB[3]: Type = EFI_HOB_TYPE_GUID_EXTENSION, Offset = 0x88, Length = 0xA0
[8001 0]    Name       = 0703F912-BF8D-4E2A-BE07-AB272525C592
[8001 0]    DataLength = 0x88
[8001 0] There are totally 4 Hobs, the End Hob address is 7AEFF38
[8001 0] MmRegisterProtocolNotify - MmConfigurationMmProtocol
[8001 0] MmDispatchFvs: FV[0] address = 0x7003000, size = 0x2FD000
[8001 0] MmCoreFfsFindMmDriver - 0x7003000
[8001 0] FvIsBeingProcessed - 0x07003000
[8001 0] Processing compressed firmware volume (AuthenticationStatus == 0)
[8001 0] MmCoreFfsFindMmDriver - 0x7AD9010
[8001 0] FvIsBeingProcessed - 0x07AD9010
[8001 0] Check MmFileTypes - 0xE
[8001 0] Find PE data - 0x7AD90AC
[8001 0] MmAddToDriverList - 58F7A62B-6280-42A7-BC38-10535A64A92C (0x07AD90AC)
[8001 0] Check MmFileTypes - 0xE
[8001 0] MmDispatcher
[8001 0]   Drain the Scheduled Queue
[8001 0]   Search DriverList for items to place on Scheduled Queue
[8001 0]   DriverEntry (Discovered) - 58F7A62B-6280-42A7-BC38-10535A64A92C
[8001 0] Evaluate MM DEPEX for FFS(58F7A62B-6280-42A7-BC38-10535A64A92C)
[8001 0]   TRUE
[8001 0]   END
[8001 0]   RESULT = TRUE
[8001 0]   Drain the Scheduled Queue
[8001 0]   DriverEntry (Scheduled) - 58F7A62B-6280-42A7-BC38-10535A64A92C
[8001 0] MmLoadImage - 58F7A62B-6280-42A7-BC38-10535A64A92C
[8001 0] UpdatePeCoffPermissions: Mapping section 0 of image at 0x7AE8000 with RO-X permissions and size 0x2000
[8001 0] UpdatePeCoffPermissions: Mapping section 1 of image at 0x7AEA000 with RW-XN permissions and size 0x1000
[8001 0] UpdatePeCoffPermissions: Mapping section 2 of image at 0x7AEB000 with RO-XN permissions and size 0x1000
[8001 0] MmInstallProtocolInterface: 5B1B31A1-9562-11D2-8E3F-00A0C969723B 7AEF890
[8001 0] Loading MM driver at 0x00007AE7000 EntryPoint=0x00007AE95A8 StandaloneMmCpu.efi
[8001 0] StartImage - 0x7AE95A8 (Standalone Mode)
[8001 0] MmInstallProtocolInterface: 26EEB3DE-B689-492E-80F0-BE8BD7DA4BA7 7AEA028
[8001 0] MmConfigurationMmNotify(26EEB3DE-B689-492E-80F0-BE8BD7DA4BA7) - 7AEA028
[8001 0] MM Core registered MM Entry Point address 7008A74
[8001 0] MmInstallProtocolInterface: 6ECBD5A1-C0F8-4702-8301-4FC2C5470A51 7AEA010
[8001 0]   Search DriverList for items to place on Scheduled Queue
[8001 0]   DriverEntry (Discovered) - 58F7A62B-6280-42A7-BC38-10535A64A92C
[8001 0]   no more MM driver to dispatch, stop the dispatch request
[8001 0]   DriverEntry (Discovered) - 58F7A62B-6280-42A7-BC38-10535A64A92C
[8001 0] MmiHandlerRegister - GUID 7E6EFFFA-69B4-4C1B-A4C7-AFF9C9244FEE - Status 0
[8001 0] MmiHandlerRegister - GUID 60FF8964-E906-41D0-AFED-F241E974E08E - Status 0
[8001 0] MmiHandlerRegister - GUID F33E1BF3-980B-4BFB-A29A-B29C86453732 - Status 0
[8001 0] MmiHandlerRegister - GUID 02CE967A-DD7E-4FFC-9EE7-810CF0470880 - Status 0
[8001 0] MmiHandlerRegister - GUID 27ABF055-B1B8-4C26-8048-748F37BAA2DF - Status 0
[8001 0] MmiHandlerRegister - GUID 7CE88FB3-4BD7-4679-87A8-A8D8DEE50D2B - Status 0
[8001 0] Failed to find MM Communication Buffer HOB
[8001 0] Only Root MMI Handlers will be supported!
[8001 0] MmMain Done!
[8001 0] Shared Cpu Driver EP 7AE940C
NOTICE: Finished bootstrapping all SPs on CPU0
INFO:    BL31: Preparing for EL3 exit to normal world
INFO:    Entry point address = 0x88000000
INFO:    SPSR = 0x3c9
```

fvp-uart1.log
-------------

```
UEFI firmware (version  built at 09:37:06 on Jul  1 2025)
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/ArmPlatformPkg/PeilessSec/PeilessSec/DEBUG/PeilessSec.dll 0x88000400
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Core/Dxe/DxeMain/DEBUG/DxeCore.dll 0xFB5D9000
Loading DxeCore at 0x00FB5D8000 EntryPoint=0x00FB5E1BC4
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Core/Dxe/DxeMain/DEBUG/DxeCore.dll 0xFB5D9000
HOBLIST address in DXE = 0xFB52D018
Memory Allocation 0x00000004 0xFBFFB000 - 0xFBFFBFFF
Memory Allocation 0x00000004 0x88000000 - 0x8BFFFFFF
Memory Allocation 0x00000004 0xFBFFA000 - 0xFBFFAFFF
Memory Allocation 0x00000004 0xFBFF9000 - 0xFBFF9FFF
Memory Allocation 0x00000004 0xFBFF8000 - 0xFBFF8FFF
Memory Allocation 0x00000004 0xFBFF7000 - 0xFBFF7FFF
Memory Allocation 0x00000004 0xFBFF6000 - 0xFBFF6FFF
Memory Allocation 0x00000004 0xFBFF5000 - 0xFBFF5FFF
Memory Allocation 0x00000004 0xFBFF4000 - 0xFBFF4FFF
Memory Allocation 0x00000004 0xFBFF3000 - 0xFBFF3FFF
Memory Allocation 0x00000004 0xFBFF2000 - 0xFBFF2FFF
Memory Allocation 0x00000004 0xFBFFC000 - 0xFBFFFFFF
Memory Allocation 0x00000004 0xFBFE2000 - 0xFBFF1FFF
Memory Allocation 0x00000004 0xFBB00000 - 0xFBFE1FFF
Memory Allocation 0x00000004 0xFB61E000 - 0xFBAFFFFF
Memory Allocation 0x00000003 0xFB5D8000 - 0xFB61DFFF
Memory Allocation 0x00000003 0xFB5D8000 - 0xFB61DFFF
FV Hob            0x88000000 - 0x8827FFFF
FV Hob            0xFB61E000 - 0xFBAFE33F
FV2 Hob           0xFB61E000 - 0xFBAFE33F
                  87940482-FC81-41C3-87E6-399CF85AC8A0 - 9E21FD93-9C72-4C15-8C4B-E77F1DB2D792
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/PCD/Dxe/Pcd/DEBUG/PcdDxe.dll 0xFAF6E000
Loading driver at 0x000FAF6D000 EntryPoint=0x000FAF71B3C PcdDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/ArmPkg/Drivers/CpuDxe/CpuDxe/DEBUG/ArmCpuDxe.dll 0xFAF55000
Loading driver at 0x000FAF54000 EntryPoint=0x000FAF5821C ArmCpuDxe.efi
ReplaceTableEntry: splitting block entry with MMU disabled
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Core/RuntimeDxe/RuntimeDxe/DEBUG/RuntimeDxe.dll 0xFAED0000
Loading driver at 0x000FAEC0000 EntryPoint=0x000FAED1A38 RuntimeDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/SecurityStubDxe/SecurityStubDxe/DEBUG/SecurityStubDxe.dll 0xFAF4B000
Loading driver at 0x000FAF4A000 EntryPoint=0x000FAF4EB68 SecurityStubDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/ResetSystemRuntimeDxe/ResetSystemRuntimeDxe/DEBUG/ResetSystemRuntimeDxe.dll 0xFADE0000
Loading driver at 0x000FADD0000 EntryPoint=0x000FADE1C50 ResetSystemRuntimeDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/EmbeddedPkg/MetronomeDxe/MetronomeDxe/DEBUG/MetronomeDxe.dll 0xFAF62000
Loading driver at 0x000FAF61000 EntryPoint=0x000FAF630B0 MetronomeDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/HiiDatabaseDxe/HiiDatabaseDxe/DEBUG/HiiDatabase.dll 0xFAE53000
Loading driver at 0x000FAE52000 EntryPoint=0x000FAE567B0 HiiDatabase.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/Acpi/AcpiTableDxe/AcpiTableDxe/DEBUG/AcpiTableDxe.dll 0xFAF3C000
Loading driver at 0x000FAF3B000 EntryPoint=0x000FAF3E63C AcpiTableDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/Platform/ARM/VExpressPkg/ConfigurationManager/ConfigurationManagerDxe/ConfigurationManagerDxe/DEBUG/ConfigurationManagerDxe.dll 0xFAF36000
Loading driver at 0x000FAF35000 EntryPoint=0x000FAF378EC ConfigurationManagerDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/DynamicTablesPkg/Drivers/DynamicTableFactoryDxe/DynamicTableFactoryDxe/DEBUG/DynamicTableFactoryDxe.dll 0xFAD10000
Loading driver at 0x000FAD0F000 EntryPoint=0x000FAD12998 DynamicTableFactoryDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/SerialDxe/SerialDxe/DEBUG/SerialDxe.dll 0xFAF31000
Loading driver at 0x000FAF30000 EntryPoint=0x000FAF32694 SerialDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/EmbeddedPkg/Universal/MmcDxe/MmcDxe/DEBUG/MmcDxe.dll 0xFAF1C000
Loading driver at 0x000FAF1B000 EntryPoint=0x000FAF20178 MmcDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/SmbiosDxe/SmbiosDxe/DEBUG/SmbiosDxe.dll 0xFAF43000
Loading driver at 0x000FAF42000 EntryPoint=0x000FAF45D94 SmbiosDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/DevicePathDxe/DevicePathDxe/DEBUG/DevicePathDxe.dll 0xFAE36000
Loading driver at 0x000FAE35000 EntryPoint=0x000FAE3DC78 DevicePathDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/ArmPkg/Drivers/ArmPciCpuIo2Dxe/ArmPciCpuIo2Dxe/DEBUG/ArmPciCpuIo2Dxe.dll 0xFAF17000
Loading driver at 0x000FAF16000 EntryPoint=0x000FAF18528 ArmPciCpuIo2Dxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/FaultTolerantWriteDxe/FaultTolerantWriteDxe/DEBUG/FaultTolerantWriteDxe.dll 0xFAE4B000
Loading driver at 0x000FAE4A000 EntryPoint=0x000FAE4EAC0 FaultTolerantWriteDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/DynamicTablesPkg/Drivers/DynamicTableManagerDxe/DynamicTableManagerDxe/DEBUG/DynamicTableManagerDxe.dll 0xFAF11000
Loading driver at 0x000FAF10000 EntryPoint=0x000FAF12940 DynamicTableManagerDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/ArmPkg/Drivers/ArmGicDxe/ArmGicDxe/DEBUG/ArmGicDxe.dll 0xFAE44000
Loading driver at 0x000FAE43000 EntryPoint=0x000FAE45E2C ArmGicDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/Platform/ARM/Drivers/NorFlashDxe/NorFlashDxe/DEBUG/NorFlashDxe.dll 0xFAC80000
Loading driver at 0x000FAC70000 EntryPoint=0x000FAC83100 NorFlashDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/Platform/ARM/VExpressPkg/Drivers/PL180MciDxe/PL180MciDxe/DEBUG/PL180MciDxe.dll 0xFAD74000
Loading driver at 0x000FAD73000 EntryPoint=0x000FAD75B10 PL180MciDxe.efi
Probing ID registers at 0x1C050FE0 for a PL180
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/BootManagerPolicyDxe/BootManagerPolicyDxe/DEBUG/BootManagerPolicyDxe.dll 0xFAD7A000
Loading driver at 0x000FAD79000 EntryPoint=0x000FAD7C628 BootManagerPolicyDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/SetupBrowserDxe/SetupBrowserDxe/DEBUG/SetupBrowser.dll 0xFACF6000
Loading driver at 0x000FACF5000 EntryPoint=0x000FACF6D08 SetupBrowser.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/BdsDxe/BdsDxe/DEBUG/BdsDxe.dll 0xFACDD000
Loading driver at 0x000FACDC000 EntryPoint=0x000FACDDF4C BdsDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Bus/Pci/PciHostBridgeDxe/PciHostBridgeDxe/DEBUG/PciHostBridgeDxe.dll 0xFAD57000
Loading driver at 0x000FAD56000 EntryPoint=0x000FAD5D9C8 PciHostBridgeDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/Variable/RuntimeDxe/VariableRuntimeDxe/DEBUG/VariableRuntimeDxe.dll 0xFAAF0000
Loading driver at 0x000FAAE0000 EntryPoint=0x000FAAF7C18 VariableRuntimeDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/ArmPkg/Drivers/TimerDxe/TimerDxe/DEBUG/ArmTimerDxe.dll 0xFAD66000
Loading driver at 0x000FAD65000 EntryPoint=0x000FAD67250 ArmTimerDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/ArmPkg/Drivers/GenericWatchdogDxe/GenericWatchdogDxe/DEBUG/GenericWatchdogDxe.dll 0xFAD52000
Loading driver at 0x000FAD51000 EntryPoint=0x000FAD53318 GenericWatchdogDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/DisplayEngineDxe/DisplayEngineDxe/DEBUG/DisplayEngine.dll 0xFAA7B000
Loading driver at 0x000FAA7A000 EntryPoint=0x000FAA7BA04 DisplayEngine.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/CapsuleRuntimeDxe/CapsuleRuntimeDxe/DEBUG/CapsuleRuntimeDxe.dll 0xFB540000
Loading driver at 0x000FB530000 EntryPoint=0x000FB541470 CapsuleRuntimeDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/MonotonicCounterRuntimeDxe/MonotonicCounterRuntimeDxe/DEBUG/MonotonicCounterRuntimeDxe.dll 0xFAA10000
Loading driver at 0x000FAA00000 EntryPoint=0x000FAA11264 MonotonicCounterRuntimeDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/EmbeddedPkg/RealTimeClockRuntimeDxe/RealTimeClockRuntimeDxe/DEBUG/RealTimeClock.dll 0xFA9D0000
Loading driver at 0x000FA9C0000 EntryPoint=0x000FA9D1A38 RealTimeClock.efi
InitializeRealTimeClock: using default timezone/daylight settings
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/Console/ConPlatformDxe/ConPlatformDxe/DEBUG/ConPlatformDxe.dll 0xFACCE000
Loading driver at 0x000FACCD000 EntryPoint=0x000FACD08F0 ConPlatformDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/Console/ConSplitterDxe/ConSplitterDxe/DEBUG/ConSplitterDxe.dll 0xFAB36000
Loading driver at 0x000FAB35000 EntryPoint=0x000FAB3BA80 ConSplitterDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/Console/GraphicsConsoleDxe/GraphicsConsoleDxe/DEBUG/GraphicsConsoleDxe.dll 0xFAA72000
Loading driver at 0x000FAA71000 EntryPoint=0x000FAA74F28 GraphicsConsoleDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/Console/TerminalDxe/TerminalDxe/DEBUG/TerminalDxe.dll 0xFAA67000
Loading driver at 0x000FAA66000 EntryPoint=0x000FAA6CE44 TerminalDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/ArmPkg/Filesystem/SemihostFs/SemihostFs/DEBUG/SemihostFs.dll 0xFAA60000
Loading driver at 0x000FAA5F000 EntryPoint=0x000FAA62A08 SemihostFs.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/Disk/DiskIoDxe/DiskIoDxe/DEBUG/DiskIoDxe.dll 0xFAA58000
Loading driver at 0x000FAA57000 EntryPoint=0x000FAA5ADD4 DiskIoDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/Disk/PartitionDxe/PartitionDxe/DEBUG/PartitionDxe.dll 0xFAA4F000
Loading driver at 0x000FAA4E000 EntryPoint=0x000FAA53598 PartitionDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/FatPkg/EnhancedFatDxe/Fat/DEBUG/Fat.dll 0xFACC1000
Loading driver at 0x000FACC0000 EntryPoint=0x000FACC8B1C Fat.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/Disk/UnicodeCollation/EnglishDxe/EnglishDxe/DEBUG/EnglishDxe.dll 0xFAB31000
Loading driver at 0x000FAB30000 EntryPoint=0x000FAB3232C EnglishDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/Platform/ARM/VExpressPkg/Drivers/ArmVExpressDxe/ArmFvpDxe/DEBUG/ArmFvpDxe.dll 0xFA9B6000
Loading driver at 0x000FA9B5000 EntryPoint=0x000FA9BB624 ArmFvpDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/OvmfPkg/VirtioBlkDxe/VirtioBlk/DEBUG/VirtioBlkDxe.dll 0xFAA42000
Loading driver at 0x000FAA41000 EntryPoint=0x000FAA44180 VirtioBlkDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Bus/Pci/PciBusDxe/PciBusDxe/DEBUG/PciBusDxe.dll 0xFA98B000
Loading driver at 0x000FA98A000 EntryPoint=0x000FA993494 PciBusDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Bus/Ata/AtaAtapiPassThru/AtaAtapiPassThru/DEBUG/AtaAtapiPassThruDxe.dll 0xFA97D000
Loading driver at 0x000FA97C000 EntryPoint=0x000FA9851EC AtaAtapiPassThruDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Bus/Ata/AtaBusDxe/AtaBusDxe/DEBUG/AtaBusDxe.dll 0xFA9A3000
Loading driver at 0x000FA9A2000 EntryPoint=0x000FA9A7568 AtaBusDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Bus/Pci/SataControllerDxe/SataControllerDxe/DEBUG/SataController.dll 0xFA977000
Loading driver at 0x000FA976000 EntryPoint=0x000FA978E4C SataController.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/FvSimpleFileSystemDxe/FvSimpleFileSystemDxe/DEBUG/FvSimpleFileSystem.dll 0xFA96E000
Loading driver at 0x000FA96D000 EntryPoint=0x000FA971CA4 FvSimpleFileSystem.efi
Process PlatformRecovery0000 (Default PlatformRecovery) ...
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 0. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 1. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 2. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 3. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 0. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 1. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 2. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 3. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 0. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 1. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 2. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 3. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 0. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 1. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 2. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 3. Must be 512B, 1KB, 2KB, or 4KB
[Bds] Unable to boot!
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 0. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 1. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 2. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 3. Must be 512B, 1KB, 2KB, or 4KB
PlatformBootManagerUnableToBoot: rebooting after refreshing all boot options
INFO:    PSCI Power Domain Map:
INFO:      Domain Node : Level 2, parent_node 4294967295, State ON (0x0)
INFO:      Domain Node : Level 1, parent_node 0, State ON (0x0)
INFO:      Domain Node : Level 1, parent_node 0, State OFF (0x2)
INFO:      CPU Node : MPID 0x0, parent_node 1, State ON (0x0)
INFO:      CPU Node : MPID 0xffffffffffffffff, parent_node 1, State OFF (0x2)
INFO:      CPU Node : MPID 0xffffffffffffffff, parent_node 1, State OFF (0x2)
INFO:      CPU Node : MPID 0xffffffffffffffff, parent_node 1, State OFF (0x2)
INFO:      CPU Node : MPID 0xffffffffffffffff, parent_node 2, State OFF (0x2)
INFO:      CPU Node : MPID 0xffffffffffffffff, parent_node 2, State OFF (0x2)
INFO:      CPU Node : MPID 0xffffffffffffffff, parent_node 2, State OFF (0x2)
INFO:      CPU Node : MPID 0xffffffffffffffff, parent_node 2, State OFF (0x2)
UEFI firmware (version  built at 09:37:06 on Jul  1 2025)
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/ArmPlatformPkg/PeilessSec/PeilessSec/DEBUG/PeilessSec.dll 0x88000400
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Core/Dxe/DxeMain/DEBUG/DxeCore.dll 0xFB5D9000
Loading DxeCore at 0x00FB5D8000 EntryPoint=0x00FB5E1BC4
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Core/Dxe/DxeMain/DEBUG/DxeCore.dll 0xFB5D9000
HOBLIST address in DXE = 0xFB52D018
Memory Allocation 0x00000004 0xFBFFB000 - 0xFBFFBFFF
Memory Allocation 0x00000004 0x88000000 - 0x8BFFFFFF
Memory Allocation 0x00000004 0xFBFFA000 - 0xFBFFAFFF
Memory Allocation 0x00000004 0xFBFF9000 - 0xFBFF9FFF
Memory Allocation 0x00000004 0xFBFF8000 - 0xFBFF8FFF
Memory Allocation 0x00000004 0xFBFF7000 - 0xFBFF7FFF
Memory Allocation 0x00000004 0xFBFF6000 - 0xFBFF6FFF
Memory Allocation 0x00000004 0xFBFF5000 - 0xFBFF5FFF
Memory Allocation 0x00000004 0xFBFF4000 - 0xFBFF4FFF
Memory Allocation 0x00000004 0xFBFF3000 - 0xFBFF3FFF
Memory Allocation 0x00000004 0xFBFF2000 - 0xFBFF2FFF
Memory Allocation 0x00000004 0xFBFFC000 - 0xFBFFFFFF
Memory Allocation 0x00000004 0xFBFE2000 - 0xFBFF1FFF
Memory Allocation 0x00000004 0xFBB00000 - 0xFBFE1FFF
Memory Allocation 0x00000004 0xFB61E000 - 0xFBAFFFFF
Memory Allocation 0x00000003 0xFB5D8000 - 0xFB61DFFF
Memory Allocation 0x00000003 0xFB5D8000 - 0xFB61DFFF
FV Hob            0x88000000 - 0x8827FFFF
FV Hob            0xFB61E000 - 0xFBAFE33F
FV2 Hob           0xFB61E000 - 0xFBAFE33F
                  87940482-FC81-41C3-87E6-399CF85AC8A0 - 9E21FD93-9C72-4C15-8C4B-E77F1DB2D792
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/PCD/Dxe/Pcd/DEBUG/PcdDxe.dll 0xFAF6E000
Loading driver at 0x000FAF6D000 EntryPoint=0x000FAF71B3C PcdDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/ArmPkg/Drivers/CpuDxe/CpuDxe/DEBUG/ArmCpuDxe.dll 0xFAF55000
Loading driver at 0x000FAF54000 EntryPoint=0x000FAF5821C ArmCpuDxe.efi
ReplaceTableEntry: splitting block entry with MMU disabled
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Core/RuntimeDxe/RuntimeDxe/DEBUG/RuntimeDxe.dll 0xFAED0000
Loading driver at 0x000FAEC0000 EntryPoint=0x000FAED1A38 RuntimeDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/SecurityStubDxe/SecurityStubDxe/DEBUG/SecurityStubDxe.dll 0xFAF4B000
Loading driver at 0x000FAF4A000 EntryPoint=0x000FAF4EB68 SecurityStubDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/ResetSystemRuntimeDxe/ResetSystemRuntimeDxe/DEBUG/ResetSystemRuntimeDxe.dll 0xFADE0000
Loading driver at 0x000FADD0000 EntryPoint=0x000FADE1C50 ResetSystemRuntimeDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/EmbeddedPkg/MetronomeDxe/MetronomeDxe/DEBUG/MetronomeDxe.dll 0xFAF62000
Loading driver at 0x000FAF61000 EntryPoint=0x000FAF630B0 MetronomeDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/HiiDatabaseDxe/HiiDatabaseDxe/DEBUG/HiiDatabase.dll 0xFAE53000
Loading driver at 0x000FAE52000 EntryPoint=0x000FAE567B0 HiiDatabase.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/Acpi/AcpiTableDxe/AcpiTableDxe/DEBUG/AcpiTableDxe.dll 0xFAF3C000
Loading driver at 0x000FAF3B000 EntryPoint=0x000FAF3E63C AcpiTableDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/Platform/ARM/VExpressPkg/ConfigurationManager/ConfigurationManagerDxe/ConfigurationManagerDxe/DEBUG/ConfigurationManagerDxe.dll 0xFAF36000
Loading driver at 0x000FAF35000 EntryPoint=0x000FAF378EC ConfigurationManagerDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/DynamicTablesPkg/Drivers/DynamicTableFactoryDxe/DynamicTableFactoryDxe/DEBUG/DynamicTableFactoryDxe.dll 0xFAD10000
Loading driver at 0x000FAD0F000 EntryPoint=0x000FAD12998 DynamicTableFactoryDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/SerialDxe/SerialDxe/DEBUG/SerialDxe.dll 0xFAF31000
Loading driver at 0x000FAF30000 EntryPoint=0x000FAF32694 SerialDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/EmbeddedPkg/Universal/MmcDxe/MmcDxe/DEBUG/MmcDxe.dll 0xFAF1C000
Loading driver at 0x000FAF1B000 EntryPoint=0x000FAF20178 MmcDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/SmbiosDxe/SmbiosDxe/DEBUG/SmbiosDxe.dll 0xFAF43000
Loading driver at 0x000FAF42000 EntryPoint=0x000FAF45D94 SmbiosDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/DevicePathDxe/DevicePathDxe/DEBUG/DevicePathDxe.dll 0xFAE36000
Loading driver at 0x000FAE35000 EntryPoint=0x000FAE3DC78 DevicePathDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/ArmPkg/Drivers/ArmPciCpuIo2Dxe/ArmPciCpuIo2Dxe/DEBUG/ArmPciCpuIo2Dxe.dll 0xFAF17000
Loading driver at 0x000FAF16000 EntryPoint=0x000FAF18528 ArmPciCpuIo2Dxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/FaultTolerantWriteDxe/FaultTolerantWriteDxe/DEBUG/FaultTolerantWriteDxe.dll 0xFAE4B000
Loading driver at 0x000FAE4A000 EntryPoint=0x000FAE4EAC0 FaultTolerantWriteDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/DynamicTablesPkg/Drivers/DynamicTableManagerDxe/DynamicTableManagerDxe/DEBUG/DynamicTableManagerDxe.dll 0xFAF11000
Loading driver at 0x000FAF10000 EntryPoint=0x000FAF12940 DynamicTableManagerDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/ArmPkg/Drivers/ArmGicDxe/ArmGicDxe/DEBUG/ArmGicDxe.dll 0xFAE44000
Loading driver at 0x000FAE43000 EntryPoint=0x000FAE45E2C ArmGicDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/Platform/ARM/Drivers/NorFlashDxe/NorFlashDxe/DEBUG/NorFlashDxe.dll 0xFAC80000
Loading driver at 0x000FAC70000 EntryPoint=0x000FAC83100 NorFlashDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/Platform/ARM/VExpressPkg/Drivers/PL180MciDxe/PL180MciDxe/DEBUG/PL180MciDxe.dll 0xFAD74000
Loading driver at 0x000FAD73000 EntryPoint=0x000FAD75B10 PL180MciDxe.efi
Probing ID registers at 0x1C050FE0 for a PL180
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/BootManagerPolicyDxe/BootManagerPolicyDxe/DEBUG/BootManagerPolicyDxe.dll 0xFAD7A000
Loading driver at 0x000FAD79000 EntryPoint=0x000FAD7C628 BootManagerPolicyDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/SetupBrowserDxe/SetupBrowserDxe/DEBUG/SetupBrowser.dll 0xFACF6000
Loading driver at 0x000FACF5000 EntryPoint=0x000FACF6D08 SetupBrowser.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/BdsDxe/BdsDxe/DEBUG/BdsDxe.dll 0xFACDD000
Loading driver at 0x000FACDC000 EntryPoint=0x000FACDDF4C BdsDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Bus/Pci/PciHostBridgeDxe/PciHostBridgeDxe/DEBUG/PciHostBridgeDxe.dll 0xFAD57000
Loading driver at 0x000FAD56000 EntryPoint=0x000FAD5D9C8 PciHostBridgeDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/Variable/RuntimeDxe/VariableRuntimeDxe/DEBUG/VariableRuntimeDxe.dll 0xFAAF0000
Loading driver at 0x000FAAE0000 EntryPoint=0x000FAAF7C18 VariableRuntimeDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/ArmPkg/Drivers/TimerDxe/TimerDxe/DEBUG/ArmTimerDxe.dll 0xFAD66000
Loading driver at 0x000FAD65000 EntryPoint=0x000FAD67250 ArmTimerDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/ArmPkg/Drivers/GenericWatchdogDxe/GenericWatchdogDxe/DEBUG/GenericWatchdogDxe.dll 0xFAD52000
Loading driver at 0x000FAD51000 EntryPoint=0x000FAD53318 GenericWatchdogDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/DisplayEngineDxe/DisplayEngineDxe/DEBUG/DisplayEngine.dll 0xFAA7B000
Loading driver at 0x000FAA7A000 EntryPoint=0x000FAA7BA04 DisplayEngine.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/CapsuleRuntimeDxe/CapsuleRuntimeDxe/DEBUG/CapsuleRuntimeDxe.dll 0xFB540000
Loading driver at 0x000FB530000 EntryPoint=0x000FB541470 CapsuleRuntimeDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/MonotonicCounterRuntimeDxe/MonotonicCounterRuntimeDxe/DEBUG/MonotonicCounterRuntimeDxe.dll 0xFAA10000
Loading driver at 0x000FAA00000 EntryPoint=0x000FAA11264 MonotonicCounterRuntimeDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/EmbeddedPkg/RealTimeClockRuntimeDxe/RealTimeClockRuntimeDxe/DEBUG/RealTimeClock.dll 0xFA9D0000
Loading driver at 0x000FA9C0000 EntryPoint=0x000FA9D1A38 RealTimeClock.efi
InitializeRealTimeClock: using default timezone/daylight settings
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/Console/ConPlatformDxe/ConPlatformDxe/DEBUG/ConPlatformDxe.dll 0xFACCE000
Loading driver at 0x000FACCD000 EntryPoint=0x000FACD08F0 ConPlatformDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/Console/ConSplitterDxe/ConSplitterDxe/DEBUG/ConSplitterDxe.dll 0xFAB36000
Loading driver at 0x000FAB35000 EntryPoint=0x000FAB3BA80 ConSplitterDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/Console/GraphicsConsoleDxe/GraphicsConsoleDxe/DEBUG/GraphicsConsoleDxe.dll 0xFAA72000
Loading driver at 0x000FAA71000 EntryPoint=0x000FAA74F28 GraphicsConsoleDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/Console/TerminalDxe/TerminalDxe/DEBUG/TerminalDxe.dll 0xFAA67000
Loading driver at 0x000FAA66000 EntryPoint=0x000FAA6CE44 TerminalDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/ArmPkg/Filesystem/SemihostFs/SemihostFs/DEBUG/SemihostFs.dll 0xFAA60000
Loading driver at 0x000FAA5F000 EntryPoint=0x000FAA62A08 SemihostFs.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/Disk/DiskIoDxe/DiskIoDxe/DEBUG/DiskIoDxe.dll 0xFAA58000
Loading driver at 0x000FAA57000 EntryPoint=0x000FAA5ADD4 DiskIoDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/Disk/PartitionDxe/PartitionDxe/DEBUG/PartitionDxe.dll 0xFAA4F000
Loading driver at 0x000FAA4E000 EntryPoint=0x000FAA53598 PartitionDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/FatPkg/EnhancedFatDxe/Fat/DEBUG/Fat.dll 0xFACC1000
Loading driver at 0x000FACC0000 EntryPoint=0x000FACC8B1C Fat.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/Disk/UnicodeCollation/EnglishDxe/EnglishDxe/DEBUG/EnglishDxe.dll 0xFAB31000
Loading driver at 0x000FAB30000 EntryPoint=0x000FAB3232C EnglishDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/Platform/ARM/VExpressPkg/Drivers/ArmVExpressDxe/ArmFvpDxe/DEBUG/ArmFvpDxe.dll 0xFA9B6000
Loading driver at 0x000FA9B5000 EntryPoint=0x000FA9BB624 ArmFvpDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/OvmfPkg/VirtioBlkDxe/VirtioBlk/DEBUG/VirtioBlkDxe.dll 0xFAA42000
Loading driver at 0x000FAA41000 EntryPoint=0x000FAA44180 VirtioBlkDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Bus/Pci/PciBusDxe/PciBusDxe/DEBUG/PciBusDxe.dll 0xFA98B000
Loading driver at 0x000FA98A000 EntryPoint=0x000FA993494 PciBusDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Bus/Ata/AtaAtapiPassThru/AtaAtapiPassThru/DEBUG/AtaAtapiPassThruDxe.dll 0xFA97D000
Loading driver at 0x000FA97C000 EntryPoint=0x000FA9851EC AtaAtapiPassThruDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Bus/Ata/AtaBusDxe/AtaBusDxe/DEBUG/AtaBusDxe.dll 0xFA9A3000
Loading driver at 0x000FA9A2000 EntryPoint=0x000FA9A7568 AtaBusDxe.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Bus/Pci/SataControllerDxe/SataControllerDxe/DEBUG/SataController.dll 0xFA977000
Loading driver at 0x000FA976000 EntryPoint=0x000FA978E4C SataController.efi
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Universal/FvSimpleFileSystemDxe/FvSimpleFileSystemDxe/DEBUG/FvSimpleFileSystem.dll 0xFA96E000
Loading driver at 0x000FA96D000 EntryPoint=0x000FA971CA4 FvSimpleFileSystem.efi
[Bds]Booting UEFI Misc Device
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 0. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 0. Must be 512B, 1KB, 2KB, or 4KB
[Bds]Booting UEFI Misc Device 2
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 1. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 1. Must be 512B, 1KB, 2KB, or 4KB
[Bds]Booting UEFI Misc Device 3
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 2. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 2. Must be 512B, 1KB, 2KB, or 4KB
[Bds]Booting UEFI Misc Device 4
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 3. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 3. Must be 512B, 1KB, 2KB, or 4KB
[Bds]Booting UEFI Non-Block Boot Device
[Bds]Booting UEFI Non-Block Boot Device 2
[Bds]Booting UEFI Non-Block Boot Device 3
Process PlatformRecovery0000 (Default PlatformRecovery) ...
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 0. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 1. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 2. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 3. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 0. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 1. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 2. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 3. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 0. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 1. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 2. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 3. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 0. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 1. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 2. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 3. Must be 512B, 1KB, 2KB, or 4KB
[Bds] Unable to boot!
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 0. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 1. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 2. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 3. Must be 512B, 1KB, 2KB, or 4KB
[Bds]Booting UiApp
add-symbol-file /data_nvme0n1/olidep01/TEMP/workspace/Build/ArmVExpress-FVP-AArch64/DEBUG_GCC5/AARCH64/MdeModulePkg/Application/UiApp/UiApp/DEBUG/UiApp.dll 0xFA039000
Loading driver at 0x000FA038000 EntryPoint=0x000FA03FBB8 UiApp.efi
[HiiDatabase]: Memory allocation is required after ReadyToBoot, which may change memory map and cause S4 resume issue.
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 0. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 1. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 2. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 3. Must be 512B, 1KB, 2KB, or 4KB
[HiiDatabase]: Memory allocation is required after ReadyToBoot, which may change memory map and cause S4 resume issue.
[HiiDatabase]: Memory allocation is required after ReadyToBoot, which may change memory map and cause S4 resume issue.
[HiiDatabase]: Memory allocation is required after ReadyToBoot, which may change memory map and cause S4 resume issue.
[HiiDatabase]: Memory allocation is required after ReadyToBoot, which may change memory map and cause S4 resume issue.
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 0. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 1. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 262144 for FAT filesystem on MediaId 2. Must be 512B, 1KB, 2KB, or 4KB
FatAllocateVolume invalid BlockIo BlockSize 65536 for FAT filesystem on MediaId 3. Must be 512B, 1KB, 2KB, or 4KB
```