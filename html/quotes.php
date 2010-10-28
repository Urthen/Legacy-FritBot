<?
    $ini = parse_ini_file('dbconfig.ini', true);
    
    $conn = mysql_connect($ini['fritbot']['host'], $ini['fritbot']['user'], $ini['fritbot']['pass']) or die ('Error connecting to mysql');

    mysql_select_db($ini['fritbot']['name']);
    
    mysql_query("SET NAMES utf8");
    mysql_query("SET CHARACTER SET utf8");
    
?>

<html>
<head>
    <link rel="StyleSheet" href="bucket.css" type="text/css" media="screen"/>
    <script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.4.2/jquery.min.js"></script> 
    <script type="text/javascript" src="jquery.tablesorter.min.js"></script>
    <script type="text/javascript" src="main.js"></script>
    <script type="text/javascript" src="tables.js"></script>
    <script language="javascript">
    
    function doForget(id) {
        xmlhttp = new XMLHttpRequest();
        xmlhttp.open("GET","forgetter.php?type=quote&id=" + id, true)
        xmlhttp.send()
    }
    
    </script>
</head>
<body>
    <img src="fritbot.jpg" title="Fuck you!" alt="Fuck you!"/>
    <div id="sidebar">
        <h2>Fritbot Nav</h2>
        <ul>
            <li><a href="bucket.htm">Manual and Changelog</a></li>
            <li><a href="factoids.php">Fact Database &amp; Management</a></li>
            <li><a href="quotes.php">Quote Database &amp; Management</a></li>
        </ul>
        <h3>Main Menu</h3>
    </div>
    <div>        
        <h1>Fritbot Quote %!</h1>
        <p>Wow, you people said some awfully stupid things! Just look at em all! 
        Click the headers to sort. To forget a quote, click it and then confirm it. Powered in part by Jimmy&reg;</p>
    </div>
    <div>    
        <table id="myTable">
            <thead><tr><th>quote</th><th>remembered by</th></tr>
            </thead>
            <tbody>
                <?
                $results = mysql_query("SELECT id, quote, author from quotes where removed is null");
                    
                while($item=mysql_fetch_array($results))
                 {
                     echo "<tr><td>" . htmlspecialchars($item['quote']) . 
                        "<div class='forgethint'>Are you sure you want to forget this? <a onclick='doForget(" . htmlspecialchars($item['id']) . ");'>Fritbot forget that!</a></div></td>"
                        . "<td>" . htmlspecialchars($item['author']) . "</td></tr>";                    
                 }
                
                ?>
            </tbody>
        </table>
    </div>
    </body>
    </html>
