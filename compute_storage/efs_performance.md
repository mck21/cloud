cloud 9 y cloudshell. dos conexiones: sesion A y sesion B

mysql -h db-mck21.csmikdkirvsq.us-east-1.rds.amazonaws.com -u admin -p

START TRANSACTION;

UPDATE cuentas SET saldo = saldo - 500 WHERE id = 1;
=======
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


task 5. Comparing file transfer tools

1st ->  4m13.261s
sh-4.2$ time rsync -r /ebs/data-1m/ /mnt/efs/rsync/${instance_id}


real    4m13.261s
user    0m23.035s
sys     0m8.666s

2nd -> 2m50.505s
sh-4.2$ time cp -r /ebs/data-1m/* /mnt/efs/cp/${instance_id}

real    2m50.505s
user    0m0.074s
sys     0m5.116s

3rd (with x4 threads (32)) -> 1m47.228s
sh-4.2$ time /usr/local/bin/fpsync -n ${threads} -v /ebs/data-1m/ /mnt/efs/fpsync/${instance_id}
which: no mail in (/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin)
1766052623 ===> Job name: 1766052623-403
1766052623 ===> Analyzing filesystem...
1766052624 ===> Waiting for sync jobs to complete...
1766052730 <===   Parts done: 3/3 (100%), remaining: 0
1766052730 <=== Time elapsed: 107s, remaining: ~0s (~35s/job)
1766052730 <=== Fpsync completed without error.

real    1m47.228s
user    0m25.162s
sys     0m9.548s

4th-> 39.400s
sh-4.2$ time find /ebs/data-1m/. -type f | parallel --will-cite -j ${threads} cp {} /mnt/efs/parallelcp

real    0m39.400s
user    0m21.310s
sys     0m23.611s


5th -> 39.694s
sh-4.2$ time parallel --will-cite -j ${threads} --pipepart --round-robin --delay .1 --block 1M -a /home/ec2-user/fpart-files-to-transfer.0 sudo "cpio -dpmL /mnt/efs/parallelcpio/${instance_id}"
1254693 blocks
1247402 blocks
1311242 blocks
1312176 blocks
1274282 blocks
1276716 blocks
1341042 blocks
1339584 blocks

real    0m39.694s
user    0m8.886s
sys     0m19.935s

-----------------------------------
tabla:
Instance name,EC2 Instance type,File transfer tool,File count,File size,Total size,Threads,Duration (in seconds),Throughput (in MB/s)
Performance Instance 3,m5.large,rsync,5000,1 MB,5 GB,1,253.261,20.21
Performance Instance 3,m5.large,cp,5000,1 MB,5 GB,1,170.505,30.02
Performance Instance 3,m5.large,fpsync,5000,1 MB,5 GB,32,107.228,47.74
Performance Instance 3,m5.large,cp + GNU Parallel,5000,1 MB,5 GB,32,39.400,129.94
Performance Instance 3,m5.large,fpart + cpio + GNU Parallel,5000,1 MB,5 GB,32,39.694,128.98


SELECT * FROM cuentas;