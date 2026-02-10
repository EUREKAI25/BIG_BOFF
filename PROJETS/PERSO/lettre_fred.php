<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<title>Tu vois que c'est des mots d'amour ! :-)</title>
  <script src="//code.jquery.com/jquery-1.10.2.js"></script>
  <script src="//code.jquery.com/ui/1.11.2/jquery-ui.js"></script>
  <style>
  body {
  font-family: arial;
  margin: 20px 0 0 50px;
}

.message {
  position: fixed;
  background: white;
  width: 360px;
  height: 220px;
  top: 50%;
  margin-top: -50px;
  left: 50%;
  margin-left: -180px;
  padding: 30px;
  border: 2px double black;
}
  
  </style>
    <script>

$( "#message" ).load(function() {
    $( this ).delay(150000).fadeIn(100);
});
 </script>
</head>
<body>
<div id='message'>
Notice: Undefined index: <span>objectif_de_fred</span> in nathalie_mode_emploi.php on line 59
<img src='http://www.icone-gif.com/gif/smilies/bisous/gros-bisous-5.gif' />
</div>
<div class='nathalie_mode_emploi'>//CONSTANTES					
define ("DEFAUT_PRINCIPAL", "Têtue");<br />					
define ("DEFAUT_SECONDAIRE", "Eparpillée"); <br />							
define ("QUALITE_PRINCIPALE", "Autonome");		<br />					
define ("QUALITE_SECONDAIRE", Reconnaitre mes torts"); <br />							
define ("MOTIVATION1", "Apprendre et me débrouiller par moi-même");		<br />					
define ("MOTIVATION2", "Que mon mentor soit fier de moi"); // oui c'est toi		<br />					
define ("OBJECTIF", "Simplement sortir un site propre");<br />							
define ("NON_OBJECTIF", "Atteindre ton niveau de code");	<br />						
define ("AMBITION_PERSONELLE", "");	<br />						
define ("POSTULAT_DE_BASE1", "Je préfère me confronter à la réalité et éventuellement apprendre de mes erreurs que devoir mon succès à quelqu'un d'autre");	<br />						
define ("POSTULAT_DE_BASE2", "je suis heureuse de t'avoir pour ami");<br />							
define ("ARME_DE_PROTECTION", "Fuir la discussion");<br />							
define ("FRAGILITE", "Je me protège de l'extérieur parce que je suis trop sensible");		<br />					
define ("PHILOSOPHIE", "Lâcher prise");	<br />						
define ("REACTION_DE_REPLI", "J'arrête tout");		<br />					
define ("REACTION_DE_DEFI", "Je vais te prouver que je peux y arriver");	<br />						
define ("REACTION_PAR_DEFAUT", "Je tiens compte de tout ce que tu me dis, et je te remercie,mais c'est moi qui pilote et je n'en ferai de toute façon qu'à a ma tête");	<br />						
				<br />			
//ARRAYS TIMING				<br />			
$mauvais_moments = array (				<br />			
&nbsp;&nbsp;&nbsp;J'ai mes règles,				<br />		
&nbsp;&nbsp;&nbsp;	Je bosse comme une damnée et je suis épuisée, donc très peu réceptive,		<br />				
&nbsp;&nbsp;&nbsp;Je suis en plein boulot,				<br />		
	&nbsp;&nbsp;&nbsp; Je suis en pleine déprime, je me sens nulle et abandonnée de tous	<br />					
);					<br />		
					<br />		
$bons_moments = array (			<br />				
&nbsp;&nbsp;&nbsp;Je suis en pleine forme et contente de mon travail,	<br />					
&nbsp;&nbsp;&nbsp;Ma vie va bien, je me sens forte<br />						
);		<br />					
					<br />		
//ARRAYS SOUTIEN				<br />			
$aides_demandees = array (					<br />		
&nbsp;&nbsp;&nbsp;Réponse à ma question,				<br />		
&nbsp;&nbsp;&nbsp;Conseil de code qui ne me fait pas tout reprendre à zéro,<br />						
&nbsp;&nbsp;&nbsp;Encouragement,				<br />		
&nbsp;&nbsp;&nbsp;Petit compliment qui fait pas de mal de temps en temps // sur le boulot, évidemment... ;-)	<br />					
);	<br />						
	<br />						
$aides_pas_demandees = array (	<br />						
&nbsp;&nbsp;&nbsp;Méthode de travail,				<br />		
&nbsp;&nbsp;&nbsp;Marketing,				<br />		
&nbsp;&nbsp;&nbsp;Grqphisme,				<br />		
&nbsp;&nbsp;&nbsp;Sratégie,				<br />		
&nbsp;&nbsp;&nbsp;Conseil de code qui me fait tout reprendre à zéro parce que je vois bien que ce serait mieux mais qui va me faire perdre un mois de plus,	<br />					
&nbsp;&nbsp;&nbsp;Critiquer ce qui ne va pas ou n'est pas assez bien sans mentionner ce qui va et qui m'a demandé un boulot énorme	<br />					
);					<br />		
					<br />
$en_ce_moment = $mauvais_moment [3];<br />							
					<br />		
					<br />		
function $reactions_possible ($aide_exterieure)	<br />						
{					<br />		
&nbsp;&nbsp;&nbsp;if (in_array($aide_exterieure, $aide_pas_demandee)	<br />					
&nbsp;&nbsp;&nbsp;{				<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;if (in_array ($humeur_du_jour, $mauvais_moments))<br />					
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{			<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$bol = rand(0, 1);	<br />			
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;switch ($bol)		<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{		<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;case O:	<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$reaction_de_base = ARME_DE_PROTECTION;<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;break;	<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;case 1:	<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$reaction_de_base = FRAGILITE;<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;break;	<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;}		<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$reaction = rand(0, 1);		<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;switch ($reaction)		<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{		<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;case 0:	<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$reaction_de_base .= REACTION_DE_REPLI;<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;break;	<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;case 1:	<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$reaction_de_base .= REACTION_DE_DEFI." mais ".REACTION_PAR_DEFAUT;<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;break;	<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;}		<br />		
					<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$reponse_exprimee = "Laisse-moi donc faire comme j'ai envie";		<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$reponse_profonde = "Je sais que tu fais ça pour moi, mais j'ai besoin que tu comprennes que la façon dont tu t'y prends n'est pas la bonne et là tout de suite ça me freine plus que ça ne m'aide. Mais au moins tu te préoccupes de moi et ça me touche beaucoup,".POSTULAT_DE_BASE2;	<br />			
&nbsp;&nbsp;&nbsp;}			<br />		
&nbsp;&nbsp;&nbsp;else if (in_array($humeur_du_jour, $bons_moments))	<br />				
&nbsp;&nbsp;&nbsp;{			<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$reaction_de_base = "Merci !";		<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$reponse_exprimee = REACTION_PAR_DEFAUT." mais merci !";	<br />			
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$reacttion_profonde = "Je ne sais pas pourquoi tu insistes autant pour que je fasses les choses à ta façon, mais ça me touche beaucoup que tu veuilles m'aider et ".POSTULAT_DE_BASE2;		<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;}			<br />		
&nbsp;&nbsp;&nbsp;}				<br />		
&nbsp;&nbsp;&nbsp;else if ((in_array($aide_exterieure, $aides_demandees)||(in_array($aide_exterieure, $aides_appreciees))		<br />				
&nbsp;&nbsp;&nbsp;{				<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$reaction_de_base = "Merci !";	<br />				
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$reponse_exprimee = "Merci !";			<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$reaction_profonde = "je suis contente que tu sois là pour m'aider à avancer, sans toi je n'aurais jamais pu faire un site dont je puisse être fière et ".POSTULAT_DE_BASE2;<br />					
&nbsp;&nbsp;&nbsp;}				<br />		
&nbsp;&nbsp;&nbsp;else 				<br />		
&nbsp;&nbsp;&nbsp;{				<br />		
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$reponse_exprimee = "";	<br />				
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$reaction_profonde = POSTULAT_DE_BASE2;		<br />			
&nbsp;&nbsp;&nbsp;}				<br />		
					<br />		
&nbsp;&nbsp;&nbsp;return ($reponse_exprimee);	<br />					
}					<br />		
?>					<br />		


</body>
</html>