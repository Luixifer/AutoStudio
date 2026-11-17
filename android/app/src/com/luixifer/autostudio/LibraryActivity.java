package com.luixifer.autostudio;
import android.app.*;
import android.os.*;
import android.content.*;
import android.widget.*;
import org.json.*;

public final class LibraryActivity extends Activity {
    @Override public void onCreate(Bundle b){super.onCreate(b);LinearLayout body=Ui.scroll(this,Ui.root(this,"Biblioteca"));Ui.para(body,"Producciones de este dispositivo. Los trabajos publicados también permanecen en GitHub; borrar la caché no borra sus resultados remotos.");JobController jobs=((AutoStudioApp)getApplication()).jobs();JSONArray history=jobs.history();
        if(history.length()==0)Ui.para(body,"Aún no hay vídeos generados desde esta instalación.");
        for(int i=0;i<history.length();i++){JSONObject item=history.optJSONObject(i);String id=item.optString("request_id");LinearLayout c=Ui.card(body);c.addView(Ui.text(this,item.optString("topic","Short"),18,true));Ui.para(c,"Solicitud "+id.substring(0,8)+" · MP4 verificado");if(jobs.video(id).isFile())Ui.button(c,"Reproducir",ViewIds.next(),true).setOnClickListener(v->startActivity(new Intent(this,PlayerActivity.class).putExtra("request_id",id)));else Ui.para(c,"La copia local se ha liberado para ahorrar espacio.");Ui.button(c,"Resultado original en GitHub",ViewIds.next(),false).setOnClickListener(v->Ui.browser(this,"https://github.com/"+GitHubClient.REPO+"/tree/video-preview/jobs/"+id));}
        LinearLayout assets=Ui.card(body);assets.addView(Ui.text(this,"Recursos visuales originales",20,true));Ui.para(assets,"La biblioteca incluye cinco ilustraciones 3D reutilizables, con hashes, resolución, procedencia y licencia en su manifiesto. No son grabaciones submarinas.");Ui.button(assets,"Abrir biblioteca de recursos",ViewIds.next(),false).setOnClickListener(v->Ui.browser(this,"https://github.com/"+GitHubClient.REPO+"/tree/main/assets/cinematic"));Ui.button(body,"Volver",ViewIds.next(),false).setOnClickListener(v->finish());
    }
    private static class ViewIds {private static int next(){return android.view.View.generateViewId();}}
}
