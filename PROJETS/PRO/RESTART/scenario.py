from functions.trace_id_generate import trace_id_generate
from config.models import model_execute
from config.config import PROMPTS
from config.prompts import get_prompt




## EURKAI
def action_validate():
    # ça suffit, pour accéder aux variables sesions exposées ?
    action = session["action"]
    prompt = session["prompt"]
    result = session["result"]
    lastaction=[action, prompt, result]
    verification = AI_check(lastaction)
    if not verification.result:
        verification.next
    print(f"verificaion {verification}")
    return verification

## STEPS        
def set_scenario_name():
    set_scenario_name = get_scenario_name(dream)
    set_session(set_scenario_name)
def set_trace_id() :
    trace_id = trace_id_generate()
    set_session(trace_id)
def step_define(dream):
    prompt = "step_define"
    result = AI_tell(prompt)
    if not result.success :
        prompt.add = result.explanation # je veux que le template prompt prévoie une zone Addendum
def set_scenario_params():
    pass

def keyframes_create():
    pass

def set_scenario_pitch():
    pass

def scenario_create():
    scenario = ""
    set_session("scenario", dict)
    scenario["name"] = set_scenario_name()
    scenario["params"] = set_scenario_params()
    scenario["pitch"] = set_scenario__pitch()
    scenario["steps"] = step_define()
    scenario["keyframes"] = keyframes_create()
    scenario["name"] = set_scenario_name()
    scenario["name"] = set_scenario_name()
    update_sessions("scenario", scenario)
    set_trace_id()
    
def set_scenario_params():
    scenario_params["color_palet"] = palet_define(prompt)

    steps = {
        "set_scenario_name" : {"output_format": {"scenario_name": str}},
        "set_scenario_params" :  {"output_format": { "shooting_brief", "acting_brief", "paletcolor"}},
        "step_define" : {"output_format": {"steps": dict}},  #on liste les étapes du scénario get_scenario_steps
        "keyframes_create": {"output_format": {"keyframes": {"name": str, "params": dict}}}, # {"scenario_pitch": list}, #pitch amélioré    get_scenario_pitch
        "palet_define" : {"global_palet": list},
        "steps_parameters": bool
    }

def app_execute():
    steps = {
        "set_scenario_name" : {"output_format": {"scenario_name": str}},
        "set_trace_id" :  {"output_format": {"trace_id": str}},
        "step_define" : {"output_format": {"steps": dict}, "next": {"action": "validate"}}, #on liste les étapes du scénario get_scenario_steps
        "scenario_create": "", # {"scenario_pitch": list}, #pitch amélioré    get_scenario_pitch
        "palet_define" : {"global_palet": list}
    }
    pass

def get_scenario_name(dream):
    scenario_name = model_execute("texttext", prompt)
    set_session({"scenario_name": scenario_name})
    pass
def get_scenario_steps(dream):
    steps = {"step": {"pitch": str}}
    set_session(steps)
    pass
def get_scenario_pitch(dream, steps):
    # return (pitch)
    pass
def get_palet(details):
    # return(global_color_palet)
    pass
def get_step_details(step, global_color_palet): 
    step_when =  {"season", "year", "hour", "month", "event", "details"}
    step_where =  {"country", "town", "scenery", "details"}
    step_emotions =  {"global", "characterA", "others"}

    step_colors = get_palet(step.pitch, step_when, step_where, step_emotions, global_color_palet)

    step_details = {
        "when":step_when,
        "where": step_where,
        "emotions" : step_emotions,
        "colors" : step_colors
    }
    # return (step_details)
    pass
    
def set_session_history(steps):
    for step in steps:
        , "status": str "to do" 
def get_session_history():
    for step in scenario_history :
        f"- {step.name} : "

expose_session()
set_session({"dream", dream})
set_session({"steps", steps})

for step in steps :
    step_define(step)
    # pour chaque étape on définit 
    # les personnages présents, l'heure et le lieu (pays ville rome), le scenery int / ext
    # l'émotion voulue pour char A, get_step_details
    # les couleurs déclinées de la palette de base (color_decline(hour, scenery) -> adapte cette palette 
    # à l'heure et le contexte int/ext)

if not history :
    pass

update_session("action") = 



      
{
    "name" = "global_prompt",
    "params" = {
        "history" : history,
        "context" : """On crée une app qui met en scène sous forme de vidéo le rêve exprimé par l'utilisateur\n
        Tu trouveras ci-dessous le rêve de l'utilisateur, de façon à lui permettre d'activer la loi d'attraction\n
        grâce aux émotions fortes que la vidéo va déclencher.\n
        Pour ça nous allons procéder par étapes :n
        {history}
        """.strip(),
        "params" : params
    }
}


 # pour chacun des briques on exécute le prompt, on fait choisir une option ou évaluer la réponse
 # à chaque fois on met l'historique en session et on le fournit à l'agent


def set_scenario(dream, ):
    pass