package com.luixifer.autostudio;
import android.app.*;
import android.os.*;
import android.content.*;
import android.text.InputType;
import android.widget.*;
import org.json.*;

public final class MainActivity extends Activity implements JobController.Listener {
    private EditText topic;private TextView status,connection;private Button generate,play,scenes,logs;private JobController jobs;
    @Override public void onCreate(Bundle saved){super.onCreate(saved);jobs=((AutoStudioApp)getApplication()).jobs();LinearLayout body=Ui.scroll(this,Ui.root(this,"AutoStudio"));
        Ui.para(body,"CONTROL DE PRODUCCIÓN · LAB 0.3\nVídeos en la nube, sin ordenador ni APIs de pago.");
        LinearLayout c=Ui.card(body);connection=Ui.para(c,"");connection.setId(Ui.CONNECTION);Ui.button(c,"Conectar / ajustes de GitHub",Ui.SETTINGS,false).setOnClickListener(v->startActivity(new Intent(this,SettingsActivity.class)));
        LinearLayout form=Ui.card(body);form.addView(Ui.text(this,"¿Qué vamos a contar?",20,true));Ui.para(form,"Esta primera versión utiliza el guion y arte gratuitos del océano profundo. Ejemplos: fuentes hidrotermales, quimiosíntesis o vida sin Sol. Otros temas y documentales aún no están habilitados.");
        topic=new EditText(this);topic.setId(Ui.TOPIC);topic.setTextSize(17);topic.setText("Vida sin Sol en el fondo del mar");topic.setHint("Tema del Short");topic.setSingleLine(true);topic.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);topic.setFilters(new android.text.InputFilter[]{new android.text.InputFilter.LengthFilter(160)});form.addView(topic,new LinearLayout.LayoutParams(-1,Ui.dp(this,58)));
        generate=Ui.button(form,"Generar Short",Ui.GENERATE,true);generate.setOnClickListener(v->{try{jobs.start(topic.getText().toString());}catch(Exception e){Ui.error(this,e.getMessage());}});
        Ui.para(form,"El tema, guion, vídeo y registros se guardan en el repositorio público Luixifer/AutoStudio. No introduzcas información privada. YouTube permanece desactivado.");
        LinearLayout progress=Ui.card(body);progress.addView(Ui.text(this,"Tu producción",20,true));status=Ui.para(progress,"Todavía no hay una producción.");status.setId(Ui.STATUS);
        Ui.button(progress,"Consultar estado",1010,false).setOnClickListener(v->jobs.refresh());
        play=Ui.button(progress,"Reproducir MP4",Ui.PLAY,true);play.setOnClickListener(v->{JSONObject s=jobs.snapshot();startActivity(new Intent(this,PlayerActivity.class).putExtra("request_id",s.optString("request_id")));});
        scenes=Ui.button(progress,"Ver escenas de este vídeo",Ui.SCENES,false);scenes.setOnClickListener(v->startActivity(new Intent(this,ScenesActivity.class).putExtra("request_id",jobs.snapshot().optString("request_id"))));
        logs=Ui.button(progress,"Ver ejecución en GitHub",1011,false);logs.setOnClickListener(v->Ui.browser(this,jobs.snapshot().optString("run_url","https://github.com/"+GitHubClient.REPO+"/actions")));
        Ui.para(progress,"Puedes cerrar la aplicación: la generación continúa en GitHub. Al volver, se consulta la misma solicitud. El móvil no renderiza el vídeo.");
        Ui.button(body,"Biblioteca y vídeos anteriores",1012,false).setOnClickListener(v->startActivity(new Intent(this,LibraryActivity.class)));
        Ui.para(body,"Sin publicación en YouTube. Documentales, producción por lotes y edición de escenas están pendientes de validar tras este primer recorrido.");
    }
    @Override protected void onStart(){super.onStart();connection.setText(new CredentialStore(this).connected()?"GitHub conectado · credencial cifrada en el dispositivo":"Primera vez: conecta GitHub para autorizar la producción.");jobs.attach(this);}
    @Override protected void onStop(){jobs.detach(this);super.onStop();}
    @Override public void changed(JSONObject state){String s=state.optString("status");status.setText(state.optString("message","Todavía no hay una producción.")+(state.has("request_id")?"\nSolicitud: "+state.optString("request_id").substring(0,8):""));generate.setEnabled(!jobs.busy());topic.setEnabled(!jobs.busy());boolean ready=s.equals("READY")&&GitHubClient.validId(state.optString("request_id"))&&jobs.video(state.optString("request_id")).isFile();play.setVisibility(ready?android.view.View.VISIBLE:android.view.View.GONE);scenes.setVisibility(ready?android.view.View.VISIBLE:android.view.View.GONE);logs.setVisibility(state.has("run_id")?android.view.View.VISIBLE:android.view.View.GONE);}
}
