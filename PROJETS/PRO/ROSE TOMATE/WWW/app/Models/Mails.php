<?php

namespace Models;
class Mails {
	const idlist = "2290a1f616"; 
	const idclient = '16ebd1e48851c053480ff89d68120244-us13';

    public static function send($the_message, $name_dest, $name_sender, $email_sender, $email_dest, $sujet)
    {
        $email_dest= "$name_dest<$email_dest>";
            $headers  = 'MIME-Version: 1.0' . "\r\n";
            $headers .= "From: $name_sender<$email_sender>" . "\r\n" ;
            $headers .= "Reply-To: $name_sender<$email_sender>" . "\r\n" ;     
            $headers .= 'Content-type: text/html; charset=UTF-8' . "\r\n";
           // $preview_text = "previou";
//echo "$name_dest, $name_sender, $email_sender, $email_dest, $sujet, $the_message";
             if (mail($email_dest, $sujet, $the_message, $headers))
             { return true; } else { return("test $name_dest, $name_sender, $email_sender, $email_dest, $sujet, ".count($the_message)); }
    }
    
	public static function sendmail ($message, $name_dest, $name_sender, $email_sender, $email_dest, $sujet)
	{ //echo "$msg, $name_dest, $name_sender, $email_sender, $email_dest, $sujet"; //return true;

            $headers  = 'MIME-Version: 1.0' . "\r\n";
            $headers .= "To: $name_dest<$email_dest>" . "\r\n" .
            $headers .= "From: $name_sender<$email_sender>" . "\r\n" .
            "Reply-To: $name_sender<$email_sender>" . "\r\n" .
            'X-Mailer: PHP/' . phpversion();       
            $headers .= 'Content-type: text/html; charset=UTF-8' . "\r\n";

            if(mail($email_dest, $sujet, $message, $headers)) {echo $message; return true; } 
     else { echo "err ds model)"; php_ini(); }
	} 

    public static function addto_list($email, $merge_fields, $idlist)
    {  
        $status = "subscribed"; //pending pour avoir un mail de confirmation
        if (empty($idlist)) { $idlist =  self::idlist;   }
        $api_key = self::idclient;
        $subscribe = self::rudr_mailchimp_subscriber_status($email, $status, $idlist, $api_key, $merge_fields );
        //return "$subscribe";

        $json_data = json_decode($subscribe); //return $jsondata;
        if ($json_data -> status == "subscribed")
         { return "ok"; } else { return ($json_data -> errors); }
    }   
    
    public static function rudr_mailchimp_subscriber_status( $email, $status, $list_id, $api_key, $merge_fields){
	$data = array(
		'apikey'        => $api_key,
        'email_address' => $email,
		'status'        => $status,
		'merge_fields'  => $merge_fields
	);
	$mch_api = curl_init(); // initialize cURL connection
 
	curl_setopt($mch_api, CURLOPT_URL, 'https://' . substr($api_key,strpos($api_key,'-')+1) . '.api.mailchimp.com/3.0/lists/' . $list_id . '/members/' . md5(strtolower($data['email_address'])));
	curl_setopt($mch_api, CURLOPT_HTTPHEADER, array('Content-Type: application/json', 'Authorization: Basic '.base64_encode( 'user:'.$api_key )));
	curl_setopt($mch_api, CURLOPT_USERAGENT, 'PHP-MCAPI/2.0');
	curl_setopt($mch_api, CURLOPT_RETURNTRANSFER, true); // return the API response
	curl_setopt($mch_api, CURLOPT_CUSTOMREQUEST, 'PUT'); // method PUT
	curl_setopt($mch_api, CURLOPT_TIMEOUT, 10);
	curl_setopt($mch_api, CURLOPT_POST, true);
	curl_setopt($mch_api, CURLOPT_SSL_VERIFYPEER, false);
	curl_setopt($mch_api, CURLOPT_POSTFIELDS, json_encode($data) ); // send data in json
 
	$result = curl_exec($mch_api);
    return $result;
}
    
    public static function mailto_webmaster($message, $user, $sujet)
    {
        if (!empty($user)) 
        {
            $email_sender = $user -> email;
        }
        else
        {
            $email_sender = "contact@rosetomate.com";
        }
            
         if (self::send($message, "Webmaster", "Rose Tomate", $email_sender, "contact@rosetomate.com", $sujet)) { return true; } else { return false; }
    }
    
    public static function del_user($email, $merge_fields, $idlist)
    {
        $status = "unsubscribed";
        if (empty($idlist)) { $idlist =  self::idlist;   }
        $api_key = self::idclient;
        $merge_fields = array();
        $unsubscribe = self::rudr_mailchimp_subscriber_status($email, $status, $idlist, $api_key, $merge_fields );
        $json_data = json_decode($unsubscribe);
        print_r($json_data);
        if ($json_data -> status == "unsubscribed")
         { return "ok"; } else { return ($json_data -> errors); }    }
    

    public static function update_mailchimp ($email, $merge_fields, $idlist)
    {
        $status = "subscribed"; //pending pour avoir un mail de confirmation
        if (empty($idlist)) { $idlist =  self::idlist;   }
        $api_key = self::idclient;

        $subscribe = self::rudr_mailchimp_subscriber_status($email, $status, $idlist, $api_key, $merge_fields );
        $json_data = json_decode($subscribe);
        if ($json_data -> status == "subscribed")
         { return "ok"; } else { return ($json_data -> errors); }
    } 

	public static function get_userinfos($email)
    {
        $status = "subscribed"; //pending pour avoir un mail de confirmation
        if (empty($idlist)) { $idlist =  self::idlist;   }
        $api_key = self::idclient;

        $subscribe = self::rudr_mailchimp_subscriber_status($email, $status, $idlist, $api_key, $merge_fields );
        
        $user = json_decode($result);
        return ($user);
    }


}