<?

$type = $_GET["type"];
$id = $_GET["id"];

echo "Ok, forgot " . $type . " #" . $id;

$ini = parse_ini_file('dbconfig.ini', true);
    
$conn = mysql_connect($ini['fritbot']['host'], $ini['fritbot']['user'], $ini['fritbot']['pass']) or die ('Error connecting to mysql');

mysql_select_db($ini['fritbot']['name']);

mysql_query("SET NAMES utf8");
mysql_query("SET CHARACTER SET utf8");

if ($type == "fact") {
    mysql_query("update factdata set removed='web' where id=".$id);
} else  {
    mysql_query("update quotes set removed='web' where id=".$id);
}
    

?>
