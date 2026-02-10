<?php

namespace Models;
class Admin {
	private $db; 
    const METHOD = 'aes-256-ctr';
    const HASH_ALGO = 'sha256';
    const SKEY = 'sdfejkv6r7twefdgef';
    const DB_HOST = 'db5000256562.hosting-data.io';
    const DB_NAME = 'dbs250376';
    const DB_USER = 'dbu190315';
    
    //FOCNTIOND BASE
    public static function encrypt ($pwd, $login)
    { 
        $secret_key = $pwd."_".$login;
        $crypted =  sha1($pwd.$secret_key);
        return $crypted;
    }
    
    //REQUETES GLOBALES
    public static function act($query, $query2,  $datas, $db, $debug)        
    {
        if ($debug == 1) { echo $query2; }       
        try{
          $requete = $db -> prepare($query);
          $requete->execute($datas);
          if ($db -> lastInsertId()){$res =$db -> lastInsertId(); }
          
        }catch(Exception $e){
           echo " Erreur ! ".$e->getMessage();
           echo " Les datas : " ;
        }     
          if ($res) { return $res;} 
          else{ return true; }        
    }

    public static function delete($table, $conds, $db, $debug)        
    {
        if ($debug == 1) 
        {print_r($conds); }

        foreach ($conds as $field => $value)
        {
            $conditions[] = "$field = '$value'";
        }
        $updates = implode("=", $updates);
        if (!empty($conds)) 
        {
            $conditions = " WHERE ".implode(" AND ", $conditions);
        }
        
        $query= "DELETE FROM $table $conditions";
        if ($debug == 1)  { echo $query; }
        if ($res = self::act($query, $query,  array(), $db, $debug) )
        { 
            return $res; 
        } else { return false; }
    } 
    
    public static function getlist($query, $query2, $datas, $debug)      
    {
        if ($debug == 1) { echo $query2; }       
        $db =\Models\Admin::db();        
        try{
          $requete = $db -> prepare($query) ;
          $requete->execute($datas) ;
          $results = $requete -> fetchAll(); //print_r($results);
          if ($debug == 1) { print_r($results);}
          if (!empty($results[0]))
          { return $results;}
            else { return false; }
        }catch(Exception $e){
           echo " Erreur ! ".$e->getMessage();
           echo " Les datas : " ;
        }        
    }
    
	public static function get_simple_ident($ident)
	{

		$a = array('À','Á','Â','Ã','Ä','Å','Æ','Ç','È','É','Ê','Ë','Ì','Í','Î','Ï','Ð','Ñ','Ò','Ó','Ô','Õ','Ö','Ø','Ù','Ú','Û','Ü','Ý','ß','à','á','â','ã','ä','å','æ','ç','è','é','ê','ë','ì','í','î','ï','ñ','ò','ó','ô','õ','ö','ø','ù','ú','û','ü','ý','ÿ','A','a','A','a','A','a','C','c','C','c','C','c','C','c','D','d','Ð','d','E','e','E','e','E','e','E','e','E','e','G','g','G','g','G','g','G','g','H','h','H','h','I','i','I','i','I','i','I','i','I','i','?','?','J','j','K','k','L','l','L','l','L','l','?','?','L','l','N','n','N','n','N','n','?','O','o','O','o','O','o','Œ','œ','R','r','R','r','R','r','S','s','S','s','S','s','Š','š','T','t','T','t','T','t','U','u','U','u','U','u','U','u','U','u','U','u','W','w','Y','y','Ÿ','Z','z','Z','z','Ž','ž','?','ƒ','O','o','U','u','A','a','I','i','O','o','U','u','U','u','U','u','U','u','U','u','?','!',':',',','.');
		$b = array('A','A','A','A','A','A','AE','C','E','E','E','E','I','I','I','I','D','N','O','O','O','O','O','O','U','U','U','U','Y','s','a','a','a','a','a','a','ae','c','e','e','e','e','i','i','i','i','n','o','o','o','o','o','o','u','u','u','u','y','y','A','a','A','a','A','a','C','c','C','c','C','c','C','c','D','d','D','d','E','e','E','e','E','e','E','e','E','e','G','g','G','g','G','g','G','g','H','h','H','h','I','i','I','i','I','i','I','i','I','i','IJ','ij','J','j','K','k','L','l','L','l','L','l','L','l','l','l','N','n','N','n','N','n','n','O','o','O','o','O','o','OE','oe','R','r','R','r','R','r','S','s','S','s','S','s','S','s','T','t','T','t','T','t','U','u','U','u','U','u','U','u','U','u','U','u','W','w','Y','y','Y','Z','z','Z','z','Z','z','s','f','O','o','U','u','A','a','I','i','O','o','U','u','U','u','U','u','U','u','U','u','','','','','','');
		$nident = strtolower(preg_replace(array('/[^a-zA-Z0-9 -]/','/[ -]+/','/^-|-$/'),array('','-',''),str_replace($a,$b,$ident)));
		return ($nident);
	}
        
    public static function test_one_record($records, $table, $debug) 
    {
        $db = self::db();
        $champs = array_keys($records);
        $tests = array();
        foreach ($records as $key => $value)
        {  $tests[] = "$key = '$value'"; }    
        $tests = implode (" AND ", $tests);
        $query = "SELECT COUNT(".$champs[0].") nb FROM $table 
        WHERE $tests ";
        if ($debug==1) {echo "$query ";}
        
        try{
              $requete = $db -> prepare($query) ;
              $requete->execute($datas) ;
              $results = $requete -> fetchAll();
               $nb = $results[0] -> nb;   if ($debug==1) {echo "$nb results <br>";}
                if ($nb==0) {  return true; } else { return false; }
            }catch(Exception $e){
               echo " Erreur ! ".$e->getMessage();
               echo " Les datas : $query;" ;
            }        
    }

    public static function get_result($one, $query, $query2, $datas, $debug)
    {
        $db =\Models\Admin::db();        
        try{
          $requete = $db -> prepare($query) ;
          $requete->execute($datas) ;
           $results = $requete -> fetchAll();
           if ($debug==1) { echo $query2; print_r($results);}
            
           if (($results[0])&&(!empty($results[0]))) 
           { // echo "ok r0";
               if ($one== 1) { return ($results[0]); }
             else  { return ($results);}
           } else {  return false; }
        }catch(Exception $e){
           echo " Erreur query ! ".$e->getMessage();
           echo " Les datas : $query" ;
        }        
    }  
    
    public static function getrecord($array, $table, $db, $debug)
    {
        if ($debug == 1)  { print_r($array); echo "<br><br>".sizeof($array); }
        $query = "SELECT * FROM $table ";
        foreach ($array as $field => $value)
        {
            $conditions[] = "$field = '$value'";
        }
        if (!empty($array))
       { $query .= " WHERE ".implode(" AND ", $conditions);}
        if ($debug == 1) { echo "$query <br><br>"; }
        if (($result = self::get_result("", $query, $query, array(), $debug))&&(!empty($result)))
        {return ($result);} else { return false; }    
    }

    public static function insert_data($datas, $table, $debug)
    {   
        if ($debug == 1) {  print_r($datas); }
        $db = self::db();
        $fields= array_keys($datas); 
        $values = array_values($datas);
        $query = "INSERT INTO $table (".implode(",", $fields).") VALUES ('".implode("','", $values)."')";
        if ($debug ==1) { echo "$query<br>";}
        $res = self::act($query, $query, array(), $db, $debug);   
        return $res;
    }
     
    public static function nbres($datas, $field, $table, $debug)
    {
        //print_r($datas);
        foreach ($datas as $field => $value)
        {
            $conditions[] = "$field = '$value'";
        }
        if (count($datas) >0)
       { $where = " WHERE ".implode(" AND ", $conditions);}
        $query = "SELECT COUNT($field) nb FROM $table $where ";
        if ($debug == 1) { echo "$query <br><br>"; }
        if (($result = self::get_result(1, $query, $query, array(), $debug))&&(!empty($result)))
        {$nb = $result -> nb; return ($nb);} else { return false; }   
        
    }    
    
    public static function getlist_where($datas, $field, $table, $debug)
    {
        foreach ($datas as $field => $value)
        {
            $conditions[] = "$field = '$value'";
        }
        if (count($datas) >0)
       { $where = " WHERE ".implode(" AND ", $conditions);}
        $query = "SELECT * FROM $table $where ";
        if ($debug == 1) { echo "$query <br><br>"; }
        if (($result = self::get_result("", $query, $query, array(), $debug))&&(!empty($result[0])))
        {return ($result);} else { return false; }   
        
    }  
    
    public static function update($array, $table, $conds, $db, $debug)        
    {
        if(empty($db)) { $db = self::db();}
        if ($debug == 1) 
        { print_r($array); print_r($conds); }
        foreach ($array as $field => $value)
        {
            $updates[] = "$field = '$value'";
        }
        foreach ($conds as $field => $value)
        {
            $conditions[] = "$field = '$value'";
        }
        $updates = implode(", ", $updates);
        if (!empty($conds)) 
        {
            $conditions = " WHERE ".implode(" AND ", $conditions);
        }
        
        $query= "UPDATE $table SET $updates $conditions";
        if ($debug == 1)  { echo $query; }
        if ($recipe = self::act($query, $query,  array(), $db, $debug) )
        { 
            return $recipe; 
        } else { return false; }
    }   
    
    public static function lastcron($cronident, $debug)
    {        
        $db = \Models\Admin::db();
        $array = array('ident' => $cronident);
        $table= "crons";
        if ($cron = \Models\Admin::getrecord($array, $table, $db, $debug))
        {return ($cron[0]); }   else { return false; }
    }
    
    public static function lastqueries($debug)
    {
        $lastcron = self::lastcron("queries", $debug) -> last_occ;
        $query = "SELECT * FROM queries WHERE statut = 0";
        $datas = array();
        $list = \Models\Admin:: getlist($query, $query, $datas, $debug);
        return $list;
    }


    
    //REQUETES BDD SITE

    
    public static function db()
    {
        try{
        $db = new \PDO('mysql:host='.DB_HOST.'; dbname='.DB_NAME.'; charset=utf8', DB_USER, DB_PASSWORD);
         $db->setAttribute(\PDO::ATTR_ERRMODE, \PDO::ERRMODE_EXCEPTION);
         $db->setAttribute(\PDO::ATTR_DEFAULT_FETCH_MODE, \PDO::FETCH_OBJ);
            return $db;
        } catch(PDOException $e) {
            die('Erreur : ' . $e->getMessage());
        }   
        
    }
    
    public static function keywords_by ($array, $debug)
    {
        $db = self::db();
        foreach ($array as $key => $val)
        {
            $conds[] = "$key = '$val'";
        }
        $where = implode ("AND ", $conds);
        $query = "SELECT * FROM keywords WHERE $where ORDER BY keyword ASC";
        $list = self::getlist($query, $query, array(), $debug)  ;
       { return $list;}
    }
  
    public static function get_option($info, $debug)
    {
        $db = self::db();
        $query = "SELECT value FROM options WHERE info = :info";
        $query2 = "SELECT value FROM options WHERE info = '$info'";
        $datas = array(":info" => $info);
        if ($result = self::get_result(1, $query, $query2, $datas, $debug))
        {return $result; } else {return true;}
    }

    public static function get_planning_crons($debug)
    {
        $db = self::db();
        $list = self::getrecord($array, "crons", $db, $debug);  
        return ($list);
    }
  
    public static  function is_admin()
    {  return true;
            
            if (((isset($_SESSION['user_id']))&&($_SESSION['user_id']==1))
                ||
            ((isset($_COOKIE['user_id']))&&($_COOKIE['user_id']==1)))
            {
                return true;
            }

        }
    
    public static  function  checkdata($array, $debug)
    {
        if ($debug == 1) { print_r($array); }
        $regex_text = "/([A-z]){5,}\w+/";
        $regex_text2 = "[a-Z-\']";
        $regex_mail = "/^[a-zA-Z0-9.!#$%&’*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/";
        $regex_pwd="/(?=.*[A-z])(?=.*[0-9]).{6,}/"; 
        $regex_date="!^(0?\d|[12]\d|3[01])-(0?\d|1[012])-((?:19|20)\d{2})$!";
        
        foreach($array as $key =>$value) 
        { 
            $$key= htmlentities($value); 
            if ((empty($value))&&($key != "debug")) { $err["wide"][] = $key; }
        }
        
       // if (($ident)&&(!preg_match($regex_text, $ident))) {  $err["err"][] ="ident";}


        if (($dnaiss)&&(!preg_match($regex_date, $dnaiss))) {  $err["err"][] ="dnaiss"; }
        if (($parrain)&&(!preg_match($regex_text, $parrain))) {  $err["err"][] ="parrain";}
        if (($last_name)&&(!preg_match($regex_text2, $last_name))) {  $err["err"][] ="last_name";}
        if (($first_name)&&(!preg_match($regex_text2, $first_name))) {  $err["err"][] ="first_name";}
        
        if (($pwd)&&($pwd!=$pwd2)) {  $err["err"][] ="pwd2"; }
        if (($pwd)&&(!filter_var($pwd, FILTER_VALIDATE_REGEXP, array( "options"=> array( "regexp" =>$regex_pwd))))) 
        {  $err["err"][] ="pwd"; }
        if (($email)&&(!filter_var($email, FILTER_VALIDATE_EMAIL))) {  $err["err"][] ="email"; }
        if (($ident)&&(!filter_var($ident, FILTER_VALIDATE_REGEXP, array( "options"=> array( "regexp" =>$regex_text))))) 
        {  $err["err"][] ="ident"; }
        
        if ($debug == 1) { print_r($err); }
        if ((!isset($err))&&(!isset($wide))) { return false; }
        else { return $err; }
    }

    public static function list_masters($debug)
    {
        $db = self::db();
        $query = "SELECT id, propriete_main FROM proprietes WHERE propriete_main =0 AND maitre =1 ";
            
        if ($list_props = self::getlist($query, $query2, $datas, $debug))
       { return $list_props;}
    }
    
     public static function get_modo ()
    {
        return ("Nathalie");
    }
    
    public static function listmasters($debug)
    {
        $db = self::db();
        $query = "SELECT * FROM keywords WHERE (master ='' OR master = 0) AND statut =1 ORDER BY keyword ASC";
        $list = self::getlist($query, $query, array(), $debug)  ;
       { return $list;}
    }
    
    public static function list_profkwds($debug)
    {
        $db = self::db();
        $query = "SELECT * FROM `keywords` k LEFT JOIN keywords_types kt  ON kt.idkeyword = k.id  LEFT JOIN type_keywords tk ON  tk.id = kt.idtypekwd WHERE type = 'profil' ORDER BY keyword ASC";
        $query2 = "SELECT * FROM `keywords` k LEFT JOIN keywords_types kt  ON kt.idkeyword = k.id  LEFT JOIN type_keywords tk ON  tk.id = kt.idtypekwd WHERE type = 'profil' ORDER BY keyword ASC";
        $list = self::getlist($query, $query2, $datas, $debug)  ;
        return ($list);
    }
    
    public static function  list_zones_kwd($idkwd, $debug)
    {
        $db = self::db();
        $array = array("idkeyword" => $idkwd);
        $list =self::getrecord($array, "keywords_zones", $db, $debug);
        return ($list);
    }
  
    public static function  list_kw_sstypes($idkwd, $debug)
    {
        $db = self::db();
        $array = array("idkeyword" => $idkwd);
        $list =self::getrecord($array, "keywords_sst", $db, $debug);
        if ($debug == 1) { print_r($list);}
        return ($list);
    }
    
     public static function  list_kwds($idmaster, $debug)
    {
        $db = self::db();
         $query = "SELECT * FROM `keywords` k LEFT JOIN keywords_types kt  ON kt.idkeyword = k.id  LEFT JOIN type_keywords tk ON  tk.id = kt.idtypekwd WHERE master = :idmaster ORDER BY keyword ASC";
         $query2 = "SELECT * FROM `keywords` k LEFT JOIN keywords_types kt  ON kt.idkeyword = k.id  LEFT JOIN type_keywords tk ON  tk.id = kt.idtypekwd WHERE master = $idmaster ORDER BY keyword ASC";         
         $datas = array(':idmaster' => $idmaster);
         $table = "keywords";
         $list = self:: get_result("", $query, $query2, $datas, $debug);
         return ($list);    
     }
    
    public static function list_masters_sympt($debug)
    {
        $db = self::db();
        $query = "SELECT * FROM symptomes WHERE maitre =1 ";
        if ($list_sympt = self::getlist($query, $query2, $datas, $debug))
       { return $list_sympt;}
    }

    public static function list_update_props($idmaster, $debug)
    {
        $db = self::db();
        $query = "SELECT id, propriete_main FROM proprietes WHERE propriete_main =$idmaster";
        if ($debug==1) { echo "$query <br>"; }
        if ($list_props = self::getlist($query, $query2, $datas, $debug))
       { return $list_props;}
    }
    
    public static function list_update_sympt($idmaster, $debug)
    {
        $db = self::db();
        $query = "SELECT id, symptome_main, symptome FROM symptomes WHERE symptome_main =$idmaster";
        if ($debug==1) { echo "$query <br>"; }
        if ($list_sympt = self::getlist($query, $query2, $datas, $debug))
       { return $list_sympt;}
    }    
   
    public static function keyword_types($idkeyword, $debug)
    {
        $query = "SELECT * FROM `keywords` k LEFT JOIN keywords_types kt  ON kt.idkeyword = k.id  LEFT JOIN type_keywords tk ON  tk.id = kt.idtypekwd WHERE k.id = :idkeyword";
        $query2 = "SELECT * FROM `keywords` k LEFT JOIN keywords_types kt  ON kt.idkeyword = k.id  LEFT JOIN type_keywords tk ON  tk.id = kt.idtypekwd WHERE k.id = $idkeyword";
        $datas = array (":idkeyword" => $idkeyword);
        $list = self::get_result("", $query, $query2, $datas, $debug);
        return ($list);
    }
    
    public static function add_keyword($keyword, $masculin, $feminin, $idmain, $type, $destination, $debug)
    {
        if  ($debug == 1) { echo "add_keyword($keyword, $idmain, $type, $destination) <br>"; }
        $db = self::db();
        $records = array("keyword" => "$keyword","feminin" => "$feminin","masculin" => "$masculin", "master" => "$idmain", "type_kwd" => "$type", "destination" => "$destination");
        if  ($debug == 1) { print_r($records); }
        if (self::test_one_record($records, "keywords", $debug))
        {
            $records["key_ident"] = self::get_simple_ident($keyword); 
            $id = self::insert_data($records, "keywords", 0);
            if  ($debug == 1) { echo "id new keyword $id<br>";}
            return $id;
        }
        else
        {
            $id = self::getrecord($records, "keywords", $db, $debug) ->id;
            if  ($debug == 1) { echo "id already keyword ".$id."<br>"; }
            return $id;
        }
    } 
    
    public static function listkeywords($debug)
    {
        $query = "SELECT * FROM `keywords` k LEFT JOIN keywords_types kt  ON kt.idkeyword = k.id  LEFT JOIN type_keywords tk ON  tk.id = kt.idtypekwd ORDER BY keyword ASC";
        $list = self::getlist($query, $query, array(), $debug); 
        return $list;
    }
    
     public static function typekeywords($debug)
     {
         $db = self::db();
         $list = self::getrecord(array(), 'type_keywords', $db, $debug);
         return $list;
     }
    
    public static function new_chat($idsession, $iduser, $db, $debug)
    {
        $records = array("idsession" => $idsession, "statut" =>1);
                
        if (self::test_one_record($records, "chat_sessions", $debug))
        {
            
            $date_session = time(); 
            $query = "INSERT INTO chat_sessions (idsession, iduser, date_session) VALUES (:idsession, :iduser, :date_session)";        
            $query2 = "INSERT INTO chat_sessions (idsession, iduser, date_session) VALUES ($idsession, $iduser, $date_session) ";
            $datas = array(":idsession" => $idsession, ":iduser" => $iduser, ":date_session" => $date_session);
            if ($debug == 1) { echo "$query2 <br><br>"; }
            $idchat = self::act($query, $query2,  $datas, $db, $debug);
        }
        
        if (($idchat)||($idchat = self::getrecord($records, "chat_sessions", $db, $debug) -> id))
        { 
            if ($debug == 1) { echo "idchat $idchat<br><br>";}
/*            $login = \Models\Membres::get_user($iduser) -> login;
            $msg = sprintf(FIRST_ADMIN_MSG, $login);
            $records = array('idchat' => $idchat, 'msg' => $msg);
            if (self::test_one_record($records, "chat_msg"))
            {
                $iduser = 0; 
                $date_session = time();
                $query = "INSERT INTO chat_msg(idchat, iduser, date_msg, msg ) 
                VALUES (:idchat,:iduser, :date_session, :msg)";
                $query2 = "INSERT INTO chat_msg(idchat, iduser, date_msg, msg ) 
                VALUES ($idchat,$iduser, $date_session, '$msg')";
                if ($debug == 1) { echo $query2; }
                $datas= array(":idchat" => $idchat, ':iduser' => $iduser, ":msg" => $msg, ":date_session" => $date_session);
                if ($idmsg = self::act($query, $query2,  $datas, $db, $debug) )
                { if ($debug == 1) { echo "idmsg = $idmsg"; } return $idmsg; } 
            }*/
            return ($idchat);
        }
        else {return false;}         


    }
    
     public static function  affect_prop_prod($idprod, $idmaster, $debug)
     {
         if ($debug==1)  { echo "affect_prop_prod($idprod, $idmaster <br>"; }
         $records = array("idprod" => $idprod, "idkeyw" => $idmaster);
         $table = "prods_key";
         if (self::test_one_record($records, $table, $debug))
         {
             echo "on affecte $idmaster à $idprod<br>";
             $idrecord = self::insert_data($records, $table, $debug);
             if ($debug==1) { return ("idrecord  $idrecord<br>"); }
         }
     }
    
    public static function  affect_keyword_prod($idprod, $idmaster, $debug)
     {
         if ($debug==1)  { echo "affect_prop_prod($idprod, $idmaster <br>"; }
         $records = array("idprod" => $idprod, "idkeyw" => $idmaster);
         $table = "prods_key";
         if (self::test_one_record($records, $table, $debug))
         {
             if ($debug==1)  { echo "on affecte $idmaster à $idprod<br>"; }
             $idrecord = self::insert_data($records, $table, $debug);
             if ($debug==1) { return ("idrecord  $idrecord<br>"); }
         }
     }
    
    public static function note_chat($idchat, $notechat, $db, $debug)
    {
        $array = array("note" => $notechat);        
        $conds = array("id" => $idchat);        
        $query = self::update($array,"chat_sessions" , $conds, $db, $debug);  
        return true;
    }
    
    public static function close_chat($idchat, $db, $debug)
    {
        $array = array("statut" => 0);
        if (!empty($idchat))
       { $conds = array("id" => $idchat);}
        self::update($array, "chat_sessions", $conds, $db, $debug); 
        return true;
    }
    
    public static function list_chat_msg($much, $idchat, $iduser, $db, $status, $debug)
    {  //status 0 : le msg n'a pas été affiché, iduser indiqué : on récupère uniquement les réponses qu'il a reçues
        if (!empty($much)) { $limit= " LIMIT 0,$much "; }
        if ($debug == 1) { echo "idchat admin $idchat"; } 
        
        $query = "SELECT c.id, idchat, iduser, date_msg, msg, statut, login 
        FROM chat_msg c
        LEFT JOIN membres m 
        ON c.iduser = m.id 
        WHERE idchat = :idchat
        AND status = :status"; 
        $query2 = "SELECT c.id, idchat, iduser, date_msg, msg, statut, login 
        FROM chat_msg c
        LEFT JOIN membres m 
        ON c.iduser = m.id 
        WHERE idchat = $idchat
        AND statut = $status"; 

        $datas = array(":idchat" => $idchat, ":statut" => $status);
        if  (empty($iduser)) 
        {  $iduser ="0";}
//            $query .=" AND iduser != :iduser";
//            $query2 .=" AND iduser != $iduser"; 
            $datas = array(":idchat" => $idchat, ":statut" => $status,":iduser" => $iduser);
        
        $query .= " ORDER BY c.id ASC $limit";        
        $query2 .= " ORDER BY c.id ASC $limit";        

        if ($debug == 1) { echo $query2; } 
        if ($listmsg = self::getlist($query2, $query2, array(), $debug) )
        {
            $array = array("statut" => 1);
            $conds = array("idchat" => $idchat);
            self::update($array, "chat_msg", $conds, $db, $debug);
             if ($debug == 1) { print_r($listmsg); }
            return $listmsg;
        }
        else  { return false;  }
    }
    
     public static function list_chat_admin($min, $idchat, $debug)
    {
        $query = "SELECT c.id, idchat, iduser, date_msg, msg, statut, login 
        FROM chat_msg c
        LEFT JOIN membres m 
        ON c.iduser = m.id 
        WHERE idchat = :idchat";
        $query2 = "SELECT c.id, idchat, iduser, date_msg, msg, statut, login 
        FROM chat_msg c
        LEFT JOIN membres m 
        ON c.iduser = m.id 
        WHERE idchat = $idchat
         ORDER BY id ASC 
        LIMIT $min, 100";    
        if ($debug == 1) { echo $query2; } 
        if ($listmsg = self::getlist($query2, $query2, array(), $debug) )
        {
             if ($debug == 1) { print_r($listmsg); }
        }   
     else {$listmsg  ="no"; }
            return $listmsg;
         
    }
    public static function get_chat($idchat, $debug)
    {
        $db = self::db();
        $query = "SELECT cs.id, iduser, date_session, statut, note, login, m.id iduser, sexe, dnaiss FROM `chat_sessions` cs, membres m WHERE m.id=cs.iduser AND cs.id = :idchat";
        $query2 = "SELECT cs.id, iduser, date_session, statut, note, login, m.id iduser, sexe, dnaiss FROM `chat_sessions` cs, membres m WHERE m.id=cs.iduser AND cs.id = $idchat";
        $datas = array(":idchat" => $idchat); 
        $chat = self::get_result(1, $query, $query2, $datas, $debug);
        return $chat;
    }
    
    public static function  get_list_msg($idchat, $debug)
    {
        $db = self::db();
        $query = "SELECT * FROM `chat_msg` cm LEFT JOIN membres m  ON m.id = cm.iduser 
        WHERE idchat = :idchat ORDER BY cm.id ASC";
        $query2 = "SELECT * FROM `chat_msg` cm LEFT JOIN membres m  ON m.id = cm.iduser 
        WHERE idchat = $idchat ORDER BY cm.id ASC";
        $datas = array(":idchat" => $idchat);
        if ($debug == 1) { echo $query2;}
        if ($listmsg = self::getlist($query, $query2, $datas, $debug) )
        { return $listmsg; } else { return false; }
    }
 
    public static function new_action($idauthor, $iduser, $idaction, $idinfo, $debug)
    {
        $db = self::db();
        $records = array ("id_author" => $idauthor, "iduser" => $iduser, "id_info" => $idinfo, "type_news" => $idaction);
        if ($debug == 1) { print_r($records);}
        if (self::test_one_record($records, "wall_news", $debug))
        {
            $datas = array ("iduser" => $iduser, "id_info" => $idinfo, "type_news" => $idaction, "date_news" => time());
            self::insert_data($datas, "wall_news", $debug);
        }
    }

    public static function  get_crons($day)
    {
        $db = self::db();
        $array = array ($day =>1);
        $list = self:: getrecord($array, "crons", $db, 0);
        return ($list);
    }
   
    public static function get_language()
    {

        if (isset($_COOKIE['language']))
        {  $language = $_COOKIE['language']; }
        else 
        {
            $language  = "FR";
           // $language = $_SERVER['HTTP_ACCEPT_LANGUAGE'];
           // $language = strtoupper($language{0}.$language{1});            
        }
        return $language;
    }
    
	public static function voyelle($nomatester, $motaaccorder, $genre)
	{
		$voyelles = array ( 'à', 'â', 'ä', 'á', 'ã', 'å',
            'î', 'ï', 'ì', 'í', 
            'ô', 'ö', 'ò', 'ó', 'õ', 'ø', 
            'ù', 'û', 'ü', 'ú', 
            'é', 'è', 'ê', 'ë', '&eacute;', '&egrave;', '&ecirc;', 
            'ç', 'ÿ', 'ñ',  'a', 'a', 'a', 'a', 'a', 'a', 
            'i', 'i', 'i', 'i', 
            'o', 'o', 'o', 'o', 'o', 'o', 
            'u', 'u', 'u', 'u', 
            'e', 'e', 'e', 'e', 'e', 'e', 'h');

		$first =strtolower($nomatester[0]); 
		$mots = array ('macérat');
		if (in_array ($first, $voyelles))
		{
			switch ($motaaccorder)
			{
				case 'de':
					if (LANG =="FR") { return ("d'"); }
				break;	
				case 'le':
					if ((in_array($motatester, $mots))&&(LANG=="FR")) { return ('du'); } else   { return ("de l'"); }
				break;	
			}
		}
		 else 
		 { 
			switch ($motaaccorder)
			{
				case 'de':
					return $motaaccorder."&nbsp;"; 
				break;	
				case 'le':
					if ((in_array($motatester, $mots))&&(LANG=="FR")) { return ('du'); } else   { return ("de l'"); }
				break;	
			}
		}
		
	}

    public static function get_wallnews_class($news, $debug)
    {
        if ($debug == 1) { print_r($news); }
        $db = self::db();
        $class="";
        $author = \Models\Membres::get_user($news -> id_info);
        if ($author -> id == 0) { $class .= " admin"; }
        $class .= " ".$news -> ident; 
        if ($debug == 1) { echo "clss, $class"; }
        return $class;
    }

    public static function get_wallnews_photo($news, $debug)
    {
        if ($debug == 1) { print_r($news); }
        
        switch($news -> ident)
        {
            case "new_recipe":
                $idrecipe = $news -> id_info;
                $recipe = \Models\Recettes::get_recipe($idrecipe, $debug);
                $url_phot = DIR_VISUELS."rec_".$news -> iduser."_$idrecipe";
                if (!file_exists) {$url_phot = DEF_RECIPE_VIS;}
            break;
            case "welcome":
                $newuser = \Models\Membres::get_user($news-> id_info, 0);
                $action =  "Bienvenue sur Rose Tomate, ".$newuser -> login." !";
            break;  
            case "pubs":
                $action = "PUB";
            break;
            case "new_flwd":
                //print_r($news);
                $user = \Models\Membres::get_user($news -> id_flw); //
                //print_r($user);
                $url_phot = $user -> url_photo;
                   // DIR_VISUELS."prof_".$news -> id_info;
                if (empty($url_phot))
                {
                    if ($user -> sexe == 'f') {$url_phot = DEF_PROF_VIS_F;}
                    if ($user -> sexe == 'h') {$url_phot = DEF_PROF_VIS_H;}
                } 
            break;
            case "new_fill":
                $user = \Models\Membres::get_user($news -> id_info); // print_R($user);
                $url_phot = $user -> url_photo;
                   // DIR_VISUELS."prof_".$news -> id_info;
                if (empty($url_phot))
                {
                    if ($user -> sexe == 'f') {$url_phot = DEF_PROF_VIS_F;}
                    if ($user -> sexe == 'h') {$url_phot = DEF_PROF_VIS_H;}
                }  
            break;
        }
        
        if ($debug == 1) { echo "url photo, $url_phot"; }
        return $url_phot;
    }
    
    public static function premium_price($debug)
    {
        $premium_price = \Models\Admin::get_option("premium_price", $debug);
        return ($premium_price);
    }
    
    public static function get_wallnews_action($news, $debug)
    {
        $db = self::db();
        
        $author = \Models\Membres::get_user($news -> iduser);
        $iduser =$_SESSION['iduser'];
        if ($debug==1) {print_r($news);}

       // echo "test ".$news -> ident;
        switch($news -> ident)
        {
            case "new_recipe":
                $recipe = \Models\Recettes::get_recipe($news-> id_info, $debug);
                $action = $author -> login." a publié une recette de ".(strtolower($recipe -> type_recette))." : <span>".$recipe -> nom."</span>";
            break;
            case "welcome":
                $newuser = \Models\Membres::get_user($news-> iduser);
                $action =  "Bienvenue sur Rose Tomate, ".$newuser -> login." !";
            break;  
            case "pubs":
                $action = "PUB";
            break;
            case "new_flwd":
                $userconn = \Models\Membres::get_user($_SESSION['iduser']); 
                
                $user = \Models\Membres::get_user($news -> id_flw); //print_r($user);

                switch ($user -> sexe)
                {
                    case "f": $pronom = "elle"; break;
                    case "h": $pronom = "lui"; break;
                }
                $compat = \Models\Membres::compat('', $user -> id, $userconn -> id, $debug);
                if (($compat)&&(\Models\Membres::profile_ready($user -> id, $debug))&&(\Models\Membres::profile_ready($userconn -> id, $debug))&&($userconn -> idabont >1))
                {
                    $addcompat = "Vous avez un profil cosmétique similaire à $compat. <br>Voulez vous voir son profil et découvrir ce qui marche pour $pronom ?";
                }
                if ($userconn -> id_abont ==3)
                {
                    $addcompat .= "En tant que membre Premium Pro, vous toucherez désormais x% sur toutes ses ventes et x% sur tous ses achats.";
                }
                else if ($userconn -> id_abont ==3)
                {
                    $addcompat .= "Devenez membre Premium Pro avant le xx pour toucher x% sur toutes ses ventes et x% sur tous ses achats.<br><a href=''>Devenir membre Premium Pro</a>";
                }
                $action = "<a href='".HOME."perso/".$user -> id."'>".$user -> login."</a> vient de s'abonner à votre profil. $addcompat";
            break;
            case "new_fav_recipe":
                $user = \Models\Membres::get_user($news -> more); //print_r($user);
                $recipe = \Models\Recettes::get_recipe($news  -> id_info, $debug);
                $action = $user -> login." vient d'ajouter la recette <a href=''>".$recipe -> name."</a> à ses favoris.";
            break;
            case "new_fav_prod":
                $user = \Models\Membres::get_user($news -> more); //print_r($user);
                $product = \Models\Produits::get_product($idprod, $debug);
                $action = $user -> login." vient d'ajouter le produit <a href=''>".$product -> name."</a> à ses favoris.";
            break; 

            case "presa_site":
                //print_R($news); 
                $iduser = $news -> iduser;
                $user = \Models\Membres::get_user($news-> iduser, 0);
                $action = "Bonjour ".$user -> login.",<br>Votre profil n'est pas encore complet, voulez-vous le mettre à jour maintenant ? 
                <br>Dès que ce sera fait, vous pourrez découvrir les membres ont le même profil cosmétique que vous. Ainsi vous pourrez vous abonner à leur profil, 
                copier leurs recettes et vous inspirer de leurs routines !
                <div><a class='openmenu' id='perso'>Je complète mon profil</a></div>
                <div class='moreacts'>Cherchez dès maintenant les produits par propriété et créez vos recettes depuis le moteur de recherche  <span id='butmen'><i class='fas fa-plus openmenu' id='keysearch'></i></span></div>
                <div class='moreacts'>Retrouvez vos recettes et produits favoris dans votre carnet cosmétique <span id='butmen'><i class='fas fa-plus openmenu' id='recipes'></i></span></div> ";
            break;   
            case "new_fill":
                $filleul = \Models\Membres::get_user($news-> id_info, 0);
                $action = "<a href='".HOME."perso/".$filleul -> id."'>".$filleul ->login."</a> vient de s'inscrire sur Rose Tomate grâce à vous.";
            break;
        }
        if ($debug == 1) { echo "idaction, $action"; }
        if (($news -> ident != "presa_site")||(!\Models\Membres::profile_ready($iduser, 0)))
        {
            return $action;
        }
    }

    public static function get_wallnews_list ($iduser, $min, $max, $offset, $statut, $debug)
    {
        if ($debug==1) {echo "$iduser, $min, $max, $lim, $statut";}
        $db = self::db();
        if (empty($iduser)) { $iduser = $_SESSION["iduser"];}
        $flwd = \Models\Membres::followed($iduser,"", 0); 
        foreach ($flwd as $followed)
        { $authors[] = $followed -> id_flw; }
        $authors[] = 0;
        $query = "SELECT * FROM
        (SELECT wn.id, date_news, id_info, more, statut, ident, iduser  FROM `wall_news` wn LEFT JOIN type_news tn ON wn.type_news = tn.id WHERE iduser = $iduser AND id_author IN ($iduser, ".implode(',', $authors).")) base
        LEFT JOIN 
        (SELECT DISTINCT mb1.login followed, mb1.id id_flw, mb2.login, mb2.id iduserconn FROM `mb_follow` mb LEFT JOIN membres mb1 ON mb1.id = mb.followed LEFT JOIN membres mb2 ON mb2.id = mb.iduser WHERE iduser = $iduser) flw
        ON base.iduser = flw.iduserconn 
        
        ORDER BY id DESC LIMIT $max "; 
        if (!empty ($offset)) { $query .= " OFFSET $offset";}
        if ($list_news = self::getlist($query, $query, array(), $debug))  
        {return ($list_news); } else { return false; }
    }
    
    public static function get_wallnews ($id, $debug)
    {
        $db = self::db();
        if ($debug == 1)  {  echo "id $id"; }
        $query2 = "SELECT * FROM wall_news WHERE id = $id";
        $query = "SELECT * FROM wall_news WHERE id = :id";
        $datas = array(":id" => $id);
        if ($news = self::get_result($query, $query2, $datas, $debug))
        {return ($news); } else { return false; }
    }

    public static function get_prices_abont($abont, $debug)
    {
        $db = self::db();
        $array= array ("abont" =>$abont);
        $list = self::getrecord($array, "abonnements", $db, $debug);
        return $list;
    }
    
    public static function  rechdet_keywords($idzone, $idsst, $idtypek, $debug)
    {
        $query = "SELECT * FROM `keywords` k
        LEFT JOIN keywords_types kt ON kt.idkeyword = k.id
        LEFT JOIN keywords_sst ks ON ks.idkeyword = k.id
        LEFT JOIN keywords_zones kz ON kz.idkeyword = k.id
        WHERE kt.idtypekwd = :idtypek AND ks.idsstyp=:idsst AND kz.idzone= :idzone ORDER BY keyword ASC";
        $query2 = "SELECT * FROM `keywords` k
        LEFT JOIN keywords_types kt ON kt.idkeyword = k.id
        LEFT JOIN keywords_sst ks ON ks.idkeyword = k.id
        LEFT JOIN keywords_zones kz ON kz.idkeyword = k.id
        WHERE kt.idtypekwd = $idtypek AND ks.idsstyp=$idsst AND kz.idzone= $idzone ORDER BY keyword ASC";
        $datas = array(":idtypek" => $idtypek, ":idsst" => $idsst, ":idzone" => $idzone);
        $list = \Models\Admin::getlist($query, $query2, $datas, $debug);
        return ($list);
    }
 
    
}