<?php
namespace Controllers;

use MangoPay\Money;

class Admin { 
    function __construct(){

    }
    function run()  
    { 
         //print_r($_SESSION);
        if (($_COOKIE['iduser'])&&(!empty($_COOKIE['iduser'])))
        { $_SESSION['iduser'] = $_COOKIE['iduser']; }
        if ($_SESSION['iduser']>0)  {$iduser = $_SESSION['iduser'];}

        if (($iduser)&& (\Models\Membres::is_admin($iduser)))
        {   $user =  \Models\Membres::get_user($iduser);  
            // print_R($user); 
            $url =  $_SERVER['REQUEST_URI'] ;  
            //echo "ur $url";
            $route_chat =  "#^/boff/chat(/(.*))?/?#";
            $route_reset =  "#^/boff(/(.*)?)?/?#";
            $route_bdd =  "#^/boff/p=(.*)/?#";
            $route_page =  "#^/boff/p=(.*)&(.*)/?#";
            $debug= 0;

            $vObjet = new \Views\Front('Admin'); 
             
             if (preg_match($route_chat, $url, $infos))
             { //echo "ok chat";
                // print_r($infos);
                $vObjet = new \Views\Front('Chat'); 
                $list_chats = \Models\Chat::list_chats("", "", 0);
                $list_open_chats = \Models\Chat::list_chats(1, "", 0);
                $list_closed_chats = \Models\Chat::list_chats(0, "", 0);
                $vObjet ->list_chats = $list_chats;
                $vObjet ->list_open_chats = $list_open_chats;
                $vObjet ->list_closed_chats = $list_closed_chats;
                $vObjet ->page = "chat"; 
                 $idchat = $infos[2];
                 if($idchat  >0)
                 {
                    $chat = \Models\Admin::get_chat($idchat, $debug); 
                    $vObjet -> chat = $chat;
                 }

                 $idmember = $chat ->iduser;
                 $member = \Models\Membres::get_user($idmember);
                 $vObjet ->member = $member;
                 $list_msg = \Models\admin::get_list_msg($idchat, 0);
                 $vObjet -> list_msg = $list_msg;
             }
             else if (preg_match($route_page, $url, $infos))
             { //echo "ok page";
                 $page = $infos[2];
                 $vObjet = new \Views\Front($page); 
                 switch($page)
                 {
                     case "profil":
                         $listk = \Models\Admin::list_profkwds(0);
                         $vObjet -> listkwds = $listk;
                         $vObjet -> zones =\Models\Membres::list_rub(0);
                         $vObjet -> sstypes =\Models\Membres::list_sstypes(3, 0);
                         //$idzone, $idsst, $idtypek, $debug)
                         
                         foreach ($listk as $kw)
                         {
                             $vObjet -> listzones_kwd[$kw -> idkeyword] = \Models\Admin::list_zones_kwd($kw -> idkeyword, 0);
                             $vObjet -> list_kw_sstypes[$kw -> idkeyword]  =\Models\Admin::list_kw_sstypes($kw -> idkeyword, 0); 
                             
                         }
    
                    //print_r($vObjet -> list_kw_sstypes);             
                    /*$debug=1;
                    $db=\Models\Admin::db();
                    $keywords = \Models\Admin::getrecord(array(), "type_cheveux", $db, 0);
                    foreach ($keywords as $keyword)
                    {
                        $datas = array("keyword" => $keyword -> type);
                        if (\Models\Admin::test_one_record($datas, "keywords", $debug))
                        { 
                            $idk = \Models\Admin::insert_data($datas, "keywords", $debug);
                            $array =  array("idtypekwd" => 4, "idkeyword" => $idk );
                            \Models\Admin::insert_data($array, "keywords_types", $debug);
                        }
                    }*/                         
                     break;
                 }
                $vObjet ->page = $page;              
            }
             else if (preg_match($route_bdd, $url, $infos))
             { 
                 //echo "ok bdd ";
                 //print_r($infos);
                 $page = $infos[1]; 
                 if (preg_match("#^(.*)\?(.*)?#", $page, $dets))
                 {
                     $page = $dets[1];
                     $action = $dets[2];
                     //print_R($dets);
                 }
                 if (substr($page, -1) =="/") { $page = substr($page, 0, -1); }
                $vObjet ->page = $page;              
                 $vObjet = new \Views\Front($page); 
                 //echo "page $page";
                 switch($page)
                 {
                     case "planning":
                         $planning_crons = \Models\Admin::get_planning_crons(0);
                          $vObjet -> planning_crons =$planning_crons;
                     break;
                     case "bdd2":
                         $array =array ('statut' => 9);
                         $vObjet -> newkeywords = \Models\Admin::keywords_by ($array, 0);
                         $vObjet -> masters = \Models\Admin::listmasters(0);
                         foreach ($vObjet -> newkeywords as $keyword)
                         {
                            $listprods[$keyword -> id]= \Models\Produits::get_products_bykeyw($keyword -> id, 0);
                         }
                        $vObjet -> listprods = $listprods;  
                    break;
                     case "bdd":
                         $vObjet -> type_kwd= \Models\Admin::typekeywords(0);
                         $masters = \Models\Admin::listmasters(0);
                         foreach($masters as $master)
                         {  
                             $list_types[$master -> id] = \Models\Admin::keyword_types($master -> id, 0);
                              $list_child = \Models\Admin::list_kwds($master -> id, 0);
                             foreach ($list_child as $child)
                             {
                                 $listchild[$master -> id][] = $child;
                             }
                         }
                    $vObjet -> listzones_kwd[$kw -> idkeyword] = \Models\Admin::list_zones_kwd($kw -> idkeyword, 0);
                    $vObjet -> list_kw_sstypes =\Models\Admin::list_kw_sstypes($kw -> idkeyword, 0);    
                         
                         //print_R($listkeyw);
                         $vObjet -> listchild= $listchild;
                         $vObjet -> masters = $masters;
                         $vObjet -> list_types = $list_types;
                     break;
                     case "queries":
                        $db = \Models\Admin::db();
                        $vObjet -> lastqueries= \Models\Admin::lastqueries(0);
                         foreach ($vObjet -> lastqueries as $query)
                         {
                            $vObjet -> detqueries[$query -> id] = \Models\Recherches::detquery($query -> id, 0);
                         }
                         //print_r($vObjet -> detqueries);
                         //foreach ($vObjet -> lastqueries as $query)
                         $queries= \Models\Admin::getrecord(array(), "det_queries", $db, 0);
                         $totqueries = count($queries); //echo "il y a $totqueries requetes";
                         $vObjet -> getqueries['produits']=count(\Models\Admin::getrecord(array('rubrique'=> 'produits-cosmetiques'), "queries", $db, 0));
                         $vObjet -> getqueries['recettes']=count (\Models\Admin::getrecord(array('rubrique'=> 'recettes-cosmetiques'), "queries", $db, 0));
                         $vObjet -> getqueries['cats']= count(\Models\Admin::getrecord(array('typekeyword'=> 'cat', 'isit' => 1), "det_queries", $db, 0));
                         $vObjet -> getqueries['nocats']=$totqueries -  $vObjet -> getqueries['cats'] ;
                         $vObjet -> getqueries['props']=count(\Models\Admin::getrecord(array('typekeyword'=> 'prop', 'isit' => 1), "det_queries", $db, 0));
                         $vObjet -> getqueries['noprops']=$totqueries -  $vObjet -> getqueries['props'] ;
                         $vObjet -> getqueries['sympt']=count(\Models\Admin::getrecord(array('typekeyword'=> 'sympt', 'isit' => 1), "det_queries", $db, 0));
                         $vObjet -> getqueries['nosympt']=$totqueries -  $vObjet -> getqueries['sympt'] ;
                         $vObjet -> getqueries['caracs']=count(\Models\Admin::getrecord(array('typekeyword'=> 'carac', 'isit' => 1), "det_queries", $db, 0));
                         $vObjet -> getqueries['nocaracs']=$totqueries -  $vObjet -> getqueries['caracs'] ;
                         $vObjet -> getqueries['dest']=count(\Models\Admin::getrecord(array('typekeyword'=> 'dest', 'isit' => 1), "det_queries", $db, 0));
                         $vObjet -> getqueries['nodest']=$totqueries -  $vObjet -> getqueries['dest'] ;
                         
                         $vObjet -> getqueries['parf']=1;
                         $vObjet -> getqueries['noparf']=$totqueries -  $vObjet -> getqueries['parf'] ;                         
                    break;
                    case "categories":

                         $list_cats['Nouvelles catégories'] = \Models\Recherches::list_cats_byst(0, 0);
                         $list_cats['Catégories validées'] = \Models\Recherches::list_cats_byst(1, 0);
                         $list_cats['Catégories exclues'] = \Models\Recherches::list_cats_byst(9, 0);
                         $list_cats['Catégories'] = \Models\Recherches::list_cats(0);
                         

                         $listprops = \Models\Recherches::get_list_attributes ("", "", 1, 1, 0);
                         $listsympt = \Models\Recherches::get_list_attributes ("", "", 3, 1, 0);
                         $vObjet -> listprops = $listprops;
                         $vObjet -> list_cats = $list_cats;
                         $vObjet -> listsympt = $listsympt;
                        foreach($list_cats as $cattype)
                        { //print_R($cat);
                            foreach ($cattype as $cat)
                            {
                                $listprods[$cat -> id] = \Models\Produits::prods_by_cat($cat -> id, 0);
                                if (!empty($listprods[$cat -> id][0]))
                                {$vObjet -> listprods[$cat -> id] = $listprods[$cat -> id];}
                            }

                        }
                        $vObjet -> modal[] = DIR_MODALS."addprod.php";
                    break;
                    case "produits":
                        $where["status"] = 0;
                        $listprods["inactive"] = \Models\Produits::listprods_where(array("p.status" => 0), 0);
                        $listprods["active"] = \Models\Produits::listprods_where(array("p.status" => 1), 0);
                        $listprods["banned"] = \Models\Produits::listprods_where(array("p.status" => 9), 0);
                        $vObjet -> listprods = $listprods;
                        $list_cats = \Models\Recherches::list_cats(0);
                        $vObjet -> list_cats = $list_cats;
                    break;
                    case "aroma":
                         $vObjet -> list_cats = \Models\Recherches::list_cats(0);
                         $vObjet -> list_other_cats = \Models\Recherches::list_other_cats(0, 1);
                         
                         
                    break;
                    default:
                         echo "def $page";
                            
                }

             }
             else if (preg_match($route_reset, $url, $infos))
             {
                echo "admin";
                 
             }
             else
             {
                echo "else";
             }
            
             $vObjet ->page_body = "admin"; 
        }
         else
        { echo "logyou";
            $vObjet = new \Views\Front('LogAd'); 
            $vObjet ->page_body = "admin"; 
            $vObjet ->page = "logad"; 
        } 
        
    
        //print_r($vObjet);
        $debug=0;
        //$masters = \Models\Admin::list_masters(0);
        //$masters_symptomes = \Models\Admin::list_masters_sympt(0);
                    
            /*        foreach ($masters_symptomes as $master)
                    {
                        if ($debug ==1) {print_r($master); }
                    $idmaster =  \Models\Admin::add_keyword(strtolower($master -> symptome), '', '', 0, "symptome", $master -> destination, $debug);
                        
                        //on récupère les produits assocés directement ou non au master initial et on les affecte au master               
                        $prods = \Models\Recherches::get_prods_sympt_master($master -> id, $debug);
                        if ($debug == 1) {print_r($prods);}
                        foreach ($prods as $prod)
                        {
                            \Models\Admin::affect_keyword_prod($prod -> idprod, $idmaster, $debug);
                        } 
                        
                        //on récupère tous les symptômes associés au master et on les enregistre
                        $debug = 1;
                        $symptomes = \Models\Admin::list_update_sympt($master -> id, 0);
                        foreach ($symptomes as $sympt)
                        {
                            print_r($sympt);
                            //echo "on affecte ".$sympt ->symptome." à $idmaster (ex ".$master -> id.")";
            //               $symptome = \Models\Recherches::getsympt($sympt -> id, $debug);
                            $newid = \Models\Admin::add_keyword($sympt -> symptome, '', '', $idmaster, "symptome", '', $debug);              
                        }              
                        
                    }
                    */
                    /*
                    foreach ($masters as $prop)
                    {
                        $master = \Models\Recherches::getprop($prop -> id, 0);
                    $idmaster =  \Models\Admin::add_keyword(strtolower($master -> propriete), $master -> propriete_FR_M, $master -> propriete_FR_F, 0, "propriete", $debug);
                        
                        echo "on a enregister  ".$master -> propriete." $idmaster (ex ".$master -> id.")<br>";
                        
                        //on récupère les produits assocés au master initial et on les affecte au master               
                        $prods = \Models\Recherches::list_prods_master($master -> id, $debug);
                        print_r($prods);
                        foreach ($prods as $prod)
                        {
                            \Models\Admin::affect_prop_prod($prod -> idprod, $idmaster, $debug);
                        }  
                        // on enregistre ts les mots clefs associés au master
                        $props = \Models\Admin::list_update_props($master -> id, $debug);
                        foreach ($props as $prop)
                        {
                            $propriete1 = \Models\Recherches::getprop($prop -> id, $debug);
                            //print_r($propriete1);
                            $newid = \Models\Admin::add_keyword($propriete1 -> propriete, '', '', $idmaster, "propriete", $debug);
                            
                            //on récupère les produits assocés à ce mot-clef et on les affecte au master
                            $prods = \Models\Recherches::list_prods_master($propriete1 -> id, $debug);
                            foreach ($prods as $prod)
                            {
                                \Models\Admin::affect_prop_prod($prod -> id, $idmaster, $debug);
                            }                
                        }        
                    }
                    */
        //print_r($vObjet);
       $vObjet->render();          
    }
}