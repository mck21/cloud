INSTANCE 3
sh-4.2$ time for i in {1..1024}; do touch /mnt/efs/touch/${directory}/test-1.3-$i; done;

real    0m9.479s
user    0m0.713s
sys     0m0.189s

sh-4.2$ time seq 1 1024 | parallel --will-cite -j 128 touch /mnt/efs/touch/${directory}/test-1.4-{}

real    0m5.055s
user    0m4.068s
sys     0m3.600s

sh-4.2$ time seq 1 32 | parallel --will-cite -j 32 touch /mnt/efs/touch/${directory}/{}/test-1.5-{1..32}

real    0m0.569s
user    0m0.236s
sys     0m0.186s


CON nload -u M

Instancia 1
sh-4.2$ time dd if=/dev/zero of=/mnt/efs/dd/10G-dd-$(date +%Y%m%d%H%M%S.%3N) bs=1M count=10000 conv=fsync
10000+0 records in
10000+0 records out
10485760000 bytes (10 GB) copied, 50.2646 s, 209 MB/s

real    0m50.277s
user    0m0.001s
sys     0m6.109s

Instancia 2
sh-4.2$ time dd if=/dev/zero of=/mnt/efs/dd/10G-dd-$(date +%Y%m%d%H%M%S.%3N) bs=1M count=10000 conv=fsync
10000+0 records in
10000+0 records out
10485760000 bytes (10 GB) copied, 186.439 s, 56.2 MB/s

real    3m6.452s
user    0m0.002s
sys     0m7.468s

Instancia 3
sh-4.2$ time dd if=/dev/zero of=/mnt/efs/dd/10G-dd-$(date +%Y%m%d%H%M%S.%3N) bs=1M count=10000 conv=fsync
10000+0 records in
10000+0 records out
10485760000 bytes (10 GB) copied, 50.6531 s, 207 MB/s

real    0m50.664s
user    0m0.030s
sys     0m5.560s

----------------------------------------------
tabla:

Instance name,EC2 Instance Type,Data Size,Duration (in seconds),Average Throughput (in MB/s)
Performance Instance 1,t3.micro,10 GB,50.277,209
Performance Instance 2,m4.large,10 GB,186.452,56.2
Performance Instance 3,m5.large,10 GB,50.664,207

part 4.


INSTANCE 3
- Create files with a 1 MB block size and sync after each file -> 10.572s
- Create files with a 16 MB block size and sync after each file -> 10.664s
- Create files with a 1 MB block size and sync after each block -> 59.465s
- Create files with a 16 MB block size and sync after each block -> 16.182s

----------------------------------------------
table:

Instance name,EC2 Instance type,Operation,Data size,Block size,Sync frequency,Duration (in seconds),Throughput (in MB/s)
Performance Instance 3,m5.large,Create,2 GB,1 MB,After each file,10.572,193.7
Performance Instance 3,m5.large,Create,2 GB,16 MB,After each file,10.664,192.0
Performance Instance 3,m5.large,Create,2 GB,1 MB,After each block,59.465,34.4
Performance Instance 3,m5.large,Create,2 GB,16 MB,After each block,16.182,126.5


WITH MULTI-THREADING
- with 4 threads -> 15.240s
- with 16 threads -> 10.377s

----------------------------------------------
tabla:
Instance name,EC2 Instance type,Operation,Data Size,Block Size,Threads,Sync Frequency,Duration (in seconds),Average Throughput (in MB/s)
Performance Instance 3,m5.large,Create,2 GB,1 MB,4,After each block,15.240,134.4
Performance Instance 3,m5.large,Create,2 GB,1 MB,16,After each block,10.377,197.4


task 5.

