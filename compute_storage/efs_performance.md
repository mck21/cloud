cloud 9 y cloudshell. dos conexiones: sesion A y sesion B

mysql -h db-mck21.csmikdkirvsq.us-east-1.rds.amazonaws.com -u admin -p

START TRANSACTION;

UPDATE cuentas SET saldo = saldo - 500 WHERE id = 1;

SELECT * FROM cuentas;