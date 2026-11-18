package com.luixifer.autostudio;

import android.app.*;
import android.content.*;
import android.net.Uri;
import android.os.*;
import android.view.*;
import android.widget.*;
import org.json.*;
import java.io.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;

/** Personal script and image video generation, deliberately explicit PUBLIC upload consent. */
public final class CustomVideoActivity extends Activity {
    private static final int PICK=440;
    private final ArrayList<Uri> images=new ArrayList<>();
    private EditText title,narration;
    private LinearLayout imageList,videos;
    private TextView status;
    private CheckBox consent;
    private Button generate,refresh,choose;
    private final AtomicBoolean busy=new AtomicBoolean(false);
    private final Handler handler=new Handler(Looper.getMainLooper());
    private boolean active;
    private final Runnable ticker=new Runnable(){
        @Override public void run(){
            if(!active)return;
            refreshVideos();
            handler.postDelayed(this,40000);
        }
    };

    @Override public void onCreate(Bundle b){
        super.onCreate(b);
        LinearLayout root=Ui.scroll(this,Ui.root(this,"Crear vídeo propio"));
        Ui.para(root,"Escribe el título y el guion con UNA escena por línea. "
            +"Selecciona las imágenes y ordénalas para que correspondan a las frases. "
            +"La voz será Álex; el sistema hará los zooms, subtítulos y montaje.");
        LinearLayout form=Ui.card(root);
        title=new EditText(this);title.setHint("Título del Short (8–110 caracteres)");
        title.setSingleLine(true);title.setTextSize(16);
        form.addView(title,new LinearLayout.LayoutParams(-1,Ui.dp(this,56)));
        narration=new EditText(this);
        narration.setHint("Una escena por línea. Ejemplo:\nExiste un planeta más caliente que algunas estrellas.\nSe llama KELT nueve be, un gigantesco mundo gaseoso.\n...");
        narration.setTextSize(16);
        narration.setMinLines(6);narration.setGravity(Gravity.TOP);
        form.addView(narration,new LinearLayout.LayoutParams(-1,Ui.dp(this,196)));
        choose=Ui.button(form,"Seleccionar entre 2 y 12 imágenes",4401,false);
        choose.setOnClickListener(v->selectImages());
        imageList=new LinearLayout(this);imageList.setOrientation(LinearLayout.VERTICAL);
        form.addView(imageList);
        Ui.para(form,"Puedes cambiar el orden de las imágenes con los botones ↑ y ↓. "
            +"Cada escena utilizará la imagen con el mismo número.");

        consent=new CheckBox(this);
        consent.setText("Confirmo que puedo utilizar estas imágenes y autorizo expresamente su subida a mi repositorio público de GitHub, donde podrán permanecer visibles incluso tras borrar archivos.");
        consent.setTextSize(14);consent.setTextColor(Ui.INK);
        form.addView(consent,new LinearLayout.LayoutParams(-1,-2));
        generate=Ui.button(form,"Crear MP4 con Álex y mis imágenes",4402,true);
        generate.setOnClickListener(v->submit());
        Ui.para(form,"Se requiere token GitHub con Actions: lectura/escritura y Contents: lectura/escritura. "
            +"No subas fotografías privadas, documentos personales ni material ajeno sin derechos.");
        status=Ui.para(root,"Sin producción nueva.");
        refresh=Ui.button(root,"Actualizar mis vídeos",4403,false);
        refresh.setOnClickListener(v->refreshVideos());
        videos=new LinearLayout(this);videos.setOrientation(LinearLayout.VERTICAL);
        root.addView(videos);
        Ui.button(root,"Volver",4404,false).setOnClickListener(v->finish());
        showImages();
    }
    @Override protected void onStart(){
        super.onStart();active=true;handler.post(ticker);
    }
    @Override protected void onStop(){
        active=false;handler.removeCallbacks(ticker);super.onStop();
    }
    private void selectImages(){
        Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);
        i.addCategory(Intent.CATEGORY_OPENABLE);
        i.setType("image/*");
        i.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,true);
        startActivityForResult(i,PICK);
    }
    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);
        if(request!=PICK||result!=RESULT_OK||data==null)return;
        ArrayList<Uri> chosen=new ArrayList<>();
        if(data.getClipData()!=null){
            for(int i=0;i<data.getClipData().getItemCount();i++){
                Uri uri=data.getClipData().getItemAt(i).getUri();
                if(uri!=null&&!chosen.contains(uri))chosen.add(uri);
            }
        }else if(data.getData()!=null){chosen.add(data.getData());}
        if(chosen.size()<1||chosen.size()>12){
            Ui.error(this,"Selecciona un máximo de 12 imágenes.");
            return;
        }
        images.clear();images.addAll(chosen);
        for(Uri uri:chosen){
            try{
                getContentResolver().takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION);
            }catch(Exception ignored){/* Picker may only grant transient read. */}
        }
        showImages();
    }
    private void showImages(){
        if(imageList==null)return;
        imageList.removeAllViews();
        Ui.para(imageList,images.size()+" imágenes seleccionadas");
        for(int i=0;i<images.size();i++){
            final int index=i;
            LinearLayout line=new LinearLayout(this);
            line.setOrientation(LinearLayout.HORIZONTAL);
            line.setGravity(Gravity.CENTER_VERTICAL);
            ImageView thumbnail=new ImageView(this);
            thumbnail.setScaleType(ImageView.ScaleType.CENTER_CROP);
            try{thumbnail.setImageURI(images.get(i));}catch(Exception ignored){}
            line.addView(thumbnail,new LinearLayout.LayoutParams(Ui.dp(this,50),Ui.dp(this,50)));
            TextView number=Ui.text(this,"  "+(i+1),15,true);
            line.addView(number,new LinearLayout.LayoutParams(0,-2,1));
            Button up=new Button(this);up.setText("↑");up.setAllCaps(false);
            up.setEnabled(i>0);
            up.setOnClickListener(v->{Collections.swap(images,index,index-1);showImages();});
            line.addView(up,new LinearLayout.LayoutParams(Ui.dp(this,52),Ui.dp(this,50)));
            Button down=new Button(this);down.setText("↓");down.setAllCaps(false);
            down.setEnabled(i<images.size()-1);
            down.setOnClickListener(v->{Collections.swap(images,index,index+1);showImages();});
            line.addView(down,new LinearLayout.LayoutParams(Ui.dp(this,52),Ui.dp(this,50)));
            imageList.addView(line);
        }
    }
    private List<String> lines(){
        String[] raw=narration.getText().toString().trim().split("\\r?\\n");
        ArrayList<String> lines=new ArrayList<>();
        for(String line:raw)if(!line.trim().isEmpty())lines.add(line.trim());
        return lines;
    }
    private void submit(){
        List<String> scripts=lines();
        if(scripts.size()!=images.size()||scripts.size()<2||scripts.size()>12){
            Ui.error(this,"El número de párrafos del guion debe coincidir con las imágenes (2–12).");
            return;
        }
        if(!consent.isChecked()){
            Ui.error(this,"Debes autorizar expresamente el envío público de estas imágenes para crear el vídeo.");
            return;
        }
        if(!new CredentialStore(this).connected()){
            Ui.error(this,"Conecta primero GitHub desde Ajustes.");
            return;
        }
        if(!busy.compareAndSet(false,true))return;
        final String videoTitle=title.getText().toString();
        final ArrayList<Uri> selected=new ArrayList<>(images);
        generate.setEnabled(false);choose.setEnabled(false);
        status.setText("Preparando el envío…");
        AutoStudioApp.IO.execute(()->{
            try{
                String key=new CredentialStore(getApplicationContext()).load();
                PersonalUploadClient upload=new PersonalUploadClient(key);
                String request=upload.submit(getApplicationContext(),videoTitle,scripts,selected,
                    info->runOnUiThread(()->status.setText(info)));
                runOnUiThread(()->{
                    busy.set(false);generate.setEnabled(true);choose.setEnabled(true);
                    status.setText("Vídeo solicitado: "+request.substring(0,8)+". "
                        +"Ya se está generando. Aparecerá en la biblioteca cuando termine.");
                    refreshVideos();
                });
            }catch(Exception error){
                runOnUiThread(()->{
                    busy.set(false);generate.setEnabled(true);choose.setEnabled(true);
                    Ui.error(this,"No se ha completado el envío: "+error.getMessage()+
                        ". Puede haber imágenes subidas públicamente aunque no se haya iniciado la producción.");
                    status.setText("Envío incompleto. Consulta tu repositorio si quieres retirar archivos.");
                });
            }
        });
    }
    private void refreshVideos(){
        if(!active||!busy.compareAndSet(false,true))return;
        if(!new CredentialStore(this).connected()){
            busy.set(false);status.setText("Conecta GitHub para ver las producciones.");return;
        }
        refresh.setEnabled(false);
        AutoStudioApp.IO.execute(()->{
            try{
                CatalogVideoClient client=new CatalogVideoClient(
                    new CredentialStore(getApplicationContext()).load());
                JSONArray runs=client.customRuns();
                Map<String,JSONObject> available=client.videos();
                runOnUiThread(()->{
                    if(!active){busy.set(false);return;}
                    videos.removeAllViews();int count=0;
                    for(int i=0;i<runs.length()&&count<20;i++){
                        JSONObject run=runs.optJSONObject(i);
                        if(run==null)continue;
                        String id=run.optString("id");
                        if(!CatalogVideoClient.validRunId(id))continue;
                        String label=run.optString("display_title","Vídeo propio");
                        if(label.length()>140)label=label.substring(0,140);
                        File file;
                        try{file=CatalogVideoClient.local(getFilesDir(),id);}
                        catch(IOException e){continue;}
                        JSONObject artifact=available.get(id);
                        LinearLayout card=Ui.card(videos);
                        card.addView(Ui.text(this,label,16,true));
                        if(file.isFile()){
                            Ui.para(card,"Vídeo guardado · borrador personal");
                            Ui.button(card,"▶ Reproducir",View.generateViewId(),true)
                                .setOnClickListener(v->open(id));
                        }else if(artifact!=null){
                            Ui.para(card,"MP4 finalizado · disponible para descargar");
                            Ui.button(card,"Descargar y reproducir",View.generateViewId(),true)
                                .setOnClickListener(v->download(id,artifact));
                        }else if("completed".equals(run.optString("status"))){
                            Ui.para(card,"Finalizado: "+run.optString("conclusion")+
                                " · sin MP4 disponible o artefacto caducado.");
                        }else{
                            Ui.para(card,"En producción: "+run.optString("status"));
                        }
                        count++;
                    }
                    status.setText("Producciones personales recientes: "+count);
                    busy.set(false);refresh.setEnabled(true);
                });
            }catch(Exception e){
                runOnUiThread(()->{
                    busy.set(false);refresh.setEnabled(true);
                    if(active)status.setText("No se pudieron consultar los vídeos: "+e.getMessage());
                });
            }
        });
    }
    private void open(String run){
        startActivity(new Intent(this,PlayerActivity.class).putExtra("personal_run_id",run));
    }
    private void download(String run,JSONObject artifact){
        if(!busy.compareAndSet(false,true))return;
        refresh.setEnabled(false);
        status.setText("Descargando y verificando MP4…");
        AutoStudioApp.IO.execute(()->{
            try{
                CatalogVideoClient client=new CatalogVideoClient(
                    new CredentialStore(getApplicationContext()).load());
                File saved=client.download(run,artifact,getFilesDir());
                runOnUiThread(()->{
                    busy.set(false);refresh.setEnabled(true);
                    status.setText("Vídeo verificado: "+saved.length()+" bytes.");
                    open(run);refreshVideos();
                });
            }catch(Exception e){
                runOnUiThread(()->{
                    busy.set(false);refresh.setEnabled(true);
                    Ui.error(this,"Error al descargar: "+e.getMessage());
                });
            }
        });
    }
}
