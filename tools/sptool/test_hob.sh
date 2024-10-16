./sptool.py -i /home/katcap01/tf-a-tests/build/fvp/debug/cactus.bin:/home/katcap01/trusted-firmware-a/build/fvp/debug/fdts/cactus.dtb \
--pm-offset 4096 --img-offset 8192 -o \
/home/katcap01/trusted-firmware-a/build/fvp/debug/cactus-primary.pkg --hob-path ./hob.bin \
--hob-format-str "hhl"
