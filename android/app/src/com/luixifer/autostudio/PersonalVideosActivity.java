package com.luixifer.autostudio;

import android.app.*;
import android.content.*;
import android.os.*;
import android.view.*;
import android.widget.*;
import org.json.*;
import java.io.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;

/** Personal one-tap curated science videos, no GitHub browser or paid API. */
public final class PersonalVideosActivity extends Activity {
    private Spinner theme;
    private LinearLayout results;
    private TextView status;
    private Button generate,refresh;
    private final Handler ui=new Handler(Looper.getMainLooper());
    private final AtomicBoolean busy=new AtomicBoolean(false);
    private boolean active=false;
    private final Runnable ticker=new Runnable(){
        @Override public void run(){
            if(!active)return;
            load();
            ui.postDelayed(this,35000);
        }
    };

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout body=Ui.scroll(this,Ui.root(this,"Mis vídeos personales"));
        Ui.para(body,"Genera un Short con voz Álex e ilustraciones originales. "
            +"Por ahora solo hay tres temas; otros títulos necesitarán contenido nuevo. "
            +"Cada vídeo es un borrador de revisión. No publicamos automáticamente.");
        LinearLayout form=Ui.card(body);
        form.addView(Ui.text(this,"Crear un nuevo Short",20,true));
        theme=new Spinner(this);
        ArrayAdapter<String> adapter=new ArrayAdapter<>(this,
            android.R.layout.simple_spinner_item,
            new String[]{"Auroras boreales","El ADN","Volcanes"});
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        theme.setAdapter(adapter);
        form.addView(theme,new LinearLayout.LayoutParams(-1,Ui.dp(this,60)));
        generate=Ui.button(form,"Generar vídeo con Álex",2201,true);
        generate.setOnClickListener(v->dispatch());
        Ui.para(form,"El render se realiza en GitHub. Puedes cerrar la app. "
            +"Cuando termine, aparecerá debajo y lo reproducirás aquí.");
        refresh=Ui.button(body,"Actualizar vídeos",2202,false);
        refresh.setOnClickListener(v->load());
        status=Ui.para(body,"Preparando tu biblioteca personal…");
        results=new LinearLayout(this);
        results.setOrientation(LinearLayout.VERTICAL);
        body.addView(results,new LinearLayout.LayoutParams(-1,-2));
        Ui.button(body,"Volver",2203,false).setOnClickListener(v->finish());
    }

    @Override protected void onStart(){
        super.onStart();active=true;ui.post(ticker);
    }
    @Override protected void onStop(){
        active=false;ui.removeCallbacks(ticker);super.onStop();
    }
    private String selected(){
        int pos=theme.getSelectedItemPosition();
        return pos==0?"auroras":pos==1?"dna":"volcanoes";
    }
    private void dispatch(){
        if(!busy.compareAndSet(false,true))return;
        if(!new CredentialStore(this).connected()){
            busy.set(false);Ui.error(this,"Primero conecta GitHub en Ajustes.");return;
        }
        String topic=selected();
        generate.setEnabled(false);
        status.setText("Enviando producción: "+topic+"…");
        AutoStudioApp.IO.execute(()->{
            try{
                String token=new CredentialStore(getApplicationContext()).load();
                new GitHubClient(token).dispatchPersonal(topic);
                runOnUiThread(()->{
                    busy.set(false);generate.setEnabled(true);
                    status.setText("Solicitud aceptada. GitHub está preparando el vídeo. "
                        +"Se mostrará aquí cuando termine.");
                    load();
                });
            }catch(Exception ex){
                runOnUiThread(()->{
                    busy.set(false);generate.setEnabled(true);
                    Ui.error(this,"No se pudo iniciar la producción: "+ex.getMessage());
                    status.setText("No se ha enviado ningún trabajo.");
                });
            }
        });
    }
    private void load(){
        if(!active||!busy.compareAndSet(false,true))return;
        if(!new CredentialStore(this).connected()){
            busy.set(false);
            status.setText("Conecta GitHub desde Ajustes para ver tu biblioteca.");
            return;
        }
        refresh.setEnabled(false);
        AutoStudioApp.IO.execute(()->{
            try{
                CatalogVideoClient client=new CatalogVideoClient(
                    new CredentialStore(getApplicationContext()).load());
                JSONArray runs=client.runs();
                Map<String,JSONObject> available=client.videos();
                runOnUiThread(()->{
                    if(!active){busy.set(false);return;}
                    results.removeAllViews();
                    int shown=0;
                    for(int i=0;i<runs.length()&&shown<20;i++){
                        JSONObject run=runs.optJSONObject(i);
                        if(run==null)continue;
                        String id=run.optString("id");
                        if(!CatalogVideoClient.validRunId(id))continue;
                        String title=run.optString("display_title","Vídeo científico");
                        if(title.length()>140)title=title.substring(0,140);
                        JSONObject artifact=available.get(id);
                        File local;
                        try{local=CatalogVideoClient.local(getFilesDir(),id);}
                        catch(IOException ex){continue;}
                        LinearLayout card=Ui.card(results);
                        card.addView(Ui.text(this,title,17,true));
                        if(local.isFile()){
                            Ui.para(card,"Guardado en el móvil · borrador de revisión");
                            Ui.button(card,"▶ Reproducir vídeo",View.generateViewId(),true)
                                .setOnClickListener(v->open(id));
                        }else if(artifact!=null){
                            String category=CatalogVideoClient.themeFor(artifact.optString("name"));
                            Ui.para(card,"Vídeo terminado: "+category+" · pendiente de descarga");
                            Ui.button(card,"Descargar y reproducir",View.generateViewId(),true)
                                .setOnClickListener(v->download(id,artifact));
                        }else if("completed".equals(run.optString("status"))){
                            Ui.para(card,"Trabajo terminado: "+run.optString("conclusion")+
                                ". Puede no haber MP4 o haber caducado el archivo temporal.");
                        }else{
                            Ui.para(card,"Procesando en GitHub · "+run.optString("status"));
                        }
                        Ui.button(card,"Ver detalles en GitHub",View.generateViewId(),false)
                            .setOnClickListener(v->Ui.browser(this,
                                "https://github.com/"+GitHubClient.REPO+"/actions/runs/"+id));
                        shown++;
                    }
                    status.setText(shown==0?"Todavía no hay vídeos de catálogo.":
                        "Últimas "+shown+" producciones · actualización automática cada 35 s");
                    refresh.setEnabled(true);busy.set(false);
                });
            }catch(Exception e){
                runOnUiThread(()->{
                    if(active)status.setText("GitHub no responde: "+e.getMessage()+
                        ". Las copias locales no se han borrado.");
                    refresh.setEnabled(true);busy.set(false);
                });
            }
        });
    }
    private void open(String id){
        startActivity(new Intent(this,PlayerActivity.class)
            .putExtra("personal_run_id",id));
    }
    private void download(String id,JSONObject artifact){
        if(!busy.compareAndSet(false,true))return;
        refresh.setEnabled(false);generate.setEnabled(false);
        status.setText("Descargando y verificando el vídeo…");
        AutoStudioApp.IO.execute(()->{
            try{
                CatalogVideoClient client=new CatalogVideoClient(
                    new CredentialStore(getApplicationContext()).load());
                File file=client.download(id,artifact,getFilesDir());
                runOnUiThread(()->{
                    busy.set(false);refresh.setEnabled(true);generate.setEnabled(true);
                    status.setText("Vídeo descargado y verificado · "+file.length()+" bytes.");
                    open(id);
                    load();
                });
            }catch(Exception e){
                runOnUiThread(()->{
                    busy.set(false);refresh.setEnabled(true);generate.setEnabled(true);
                    Ui.error(this,"No se pudo recuperar el MP4: "+e.getMessage());
                });
            }
        });
    }
}
