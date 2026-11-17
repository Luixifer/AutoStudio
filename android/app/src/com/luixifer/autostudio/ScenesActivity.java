package com.luixifer.autostudio;
import android.app.*;
import android.os.*;
import android.widget.*;
import org.json.*;

public final class ScenesActivity extends Activity {
    private LinearLayout body;private TextView message;
    @Override public void onCreate(Bundle b){super.onCreate(b);body=Ui.scroll(this,Ui.root(this,"Escenas del Short"));message=Ui.para(body,"Recuperando el plan real de esta producción…");String id=getIntent().getStringExtra("request_id");if(!GitHubClient.validId(id)){finish();return;}
        AutoStudioApp.IO.execute(()->{try{JSONObject plan=GitHubClient.publicJson(GitHubClient.base(id)+"scene-plan.json");if(plan==null||!plan.optString("request_id").equals(id))throw new Exception();JSONArray scenes=plan.getJSONArray("scenes");runOnUiThread(()->{message.setText("Cada escena separa narración, recurso, subtítulos, efectos y transición. La duración final se mide a partir del audio. En esta versión la vista es de revisión: no edita ni regenera escenas todavía.");for(int i=0;i<scenes.length();i++){JSONObject scene=scenes.optJSONObject(i);LinearLayout c=Ui.card(body);c.addView(Ui.text(this,scene.optString("id").toUpperCase(java.util.Locale.ROOT),19,true));Ui.para(c,scene.optString("narration"));Ui.para(c,"Recurso: "+scene.optJSONObject("media").optString("asset_id")+"\nSubtítulos: máximo 3 palabras\nTransición: "+scene.optJSONObject("transition").optString("type"));}Ui.button(body,"Volver",1040,false).setOnClickListener(v->finish());});}catch(Exception e){runOnUiThread(()->message.setText("No se pudo recuperar el plan de escenas. Vuelve a abrirlo cuando tengas red."));}});
    }
}
