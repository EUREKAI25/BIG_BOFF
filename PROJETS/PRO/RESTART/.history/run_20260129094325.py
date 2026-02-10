# main.py / app.py / run.py
from Models import bootstrap_models

bootstrap_models()



from session import set_session, add_session, expose_session, update_session, SESSION
def run():
   print ("définition du scenario")

   session = SESSION
   dream = "Je rêve d'aller à Rome"
   session["dream"]= dream

   add_session("test", "ok")


if __name__ == "__main__":
   run()