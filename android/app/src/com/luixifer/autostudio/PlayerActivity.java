package com.luixifer.autostudio;
import android.app.*;
import android.os.*;
import android.content.*;
import android.net.Uri;
import android.provider.MediaStore;
import android.widget.*;
import android.view.*;
import java.io.*;

/** Native Android decoding of the actual downloaded, verified H.264/AAC MP4. */
public final class PlayerActivity extends Activity {
    private VideoView video;private File file;private TextView state;private boolean resume;private int position;
    public volatile boolean firstFrameRendered=false;public volatile boolean playbackFailed=false;
    @Override public void onCreate(Bundle b){super.onCreate(b);String id=getIntent().getStringExtra("request_id");if(!GitHubClient.validId(id)){finish();return;}file=((AutoStudioApp)getApplication()).jobs().video(id);if(!file.isFile()){Ui.error(this,"El vídeo no está en la caché. Puedes recuperarlo desde su ejecución de GitHub.");finish();return;}
        LinearLayout frame=Ui.root(this,"Tu Short");state=Ui.text(this,"Preparando el reproductor Android…",14,false);state.setPadding(Ui.dp(this,20),0,Ui.dp(this,20),Ui.dp(this,8));frame.addView(state);
        FrameLayout display=new FrameLayout(this);display.setBackgroundColor(0xff08131b);frame.addView(display,new LinearLayout.LayoutParams(-1,0,1));video=new VideoView(this);display.addView(video,new FrameLayout.LayoutParams(-1,-1,Gravity.CENTER));MediaController controls=new MediaController(this);controls.setAnchorView(video);video.setMediaController(controls);
        video.setOnPreparedListener(p->{state.setText("MP4 verificado · "+String.format(java.util.Locale.forLanguageTag("es-ES"),"%.2f s",p.getDuration()/1000.0));if(position>0)video.seekTo(position);video.start();});
        video.setOnInfoListener((p,what,extra)->{if(what==android.media.MediaPlayer.MEDIA_INFO_VIDEO_RENDERING_START)firstFrameRendered=true;return false;});
        video.setOnErrorListener((p,what,extra)->{playbackFailed=true;state.setText("Android no pudo reproducir este MP4. Prueba abrir la copia descargada con otro reproductor.");return true;});video.setVideoPath(file.getAbsolutePath());
        LinearLayout buttons=new LinearLayout(this);buttons.setOrientation(1);buttons.setPadding(Ui.dp(this,20),Ui.dp(this,8),Ui.dp(this,20),Ui.dp(this,10));frame.addView(buttons);
        Ui.button(buttons,"Guardar MP4 en Descargas",1030,true).setOnClickListener(v->save());Ui.button(buttons,"Volver al centro de control",1031,false).setOnClickListener(v->finish());
    }
    public int playbackPosition(){return video==null?0:video.getCurrentPosition();}
    @Override protected void onPause(){super.onPause();if(video!=null){position=video.getCurrentPosition();resume=video.isPlaying();video.pause();}}
    @Override protected void onResume(){super.onResume();if(video!=null&&resume){video.seekTo(position);video.start();}}
    @Override protected void onDestroy(){if(video!=null)video.stopPlayback();super.onDestroy();}
    private void save(){
        if(Build.VERSION.SDK_INT<29){Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT);i.addCategory(Intent.CATEGORY_OPENABLE);i.setType("video/mp4");i.putExtra(Intent.EXTRA_TITLE,"AutoStudio-"+file.getName());startActivityForResult(i,41);return;}
        AutoStudioApp.IO.execute(()->{Uri uri=null;try{
            ContentValues values=new ContentValues();values.put(MediaStore.Downloads.DISPLAY_NAME,"AutoStudio-"+file.getName());values.put(MediaStore.Downloads.MIME_TYPE,"video/mp4");values.put(MediaStore.Downloads.IS_PENDING,1);uri=getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI,values);if(uri==null)throw new IOException("Descargas no está disponible.");
            try(InputStream in=new FileInputStream(file);OutputStream out=getContentResolver().openOutputStream(uri)){copy(in,out);}
            ContentValues done=new ContentValues();done.put(MediaStore.Downloads.IS_PENDING,0);getContentResolver().update(uri,done,null,null);runOnUiThread(()->state.setText("Copia guardada en Descargas. El original verificado permanece en la aplicación."));
        }catch(Exception e){if(uri!=null)getContentResolver().delete(uri,null,null);runOnUiThread(()->Ui.error(this,"No se pudo guardar en Descargas. Comprueba el espacio disponible."));}});
    }
    private static void copy(InputStream in,OutputStream out) throws IOException{if(out==null)throw new IOException("No hay destino de escritura.");byte[] b=new byte[32768];int n;while((n=in.read(b))!=-1)out.write(b,0,n);}
    @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(request==41&&result==RESULT_OK&&data!=null&&data.getData()!=null){Uri uri=data.getData();AutoStudioApp.IO.execute(()->{try(InputStream in=new FileInputStream(file);OutputStream out=getContentResolver().openOutputStream(uri)){copy(in,out);runOnUiThread(()->state.setText("MP4 guardado."));}catch(Exception e){runOnUiThread(()->Ui.error(this,"No se pudo guardar el MP4."));}});}}
}
