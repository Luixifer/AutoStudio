package com.luixifer.autostudio;

import android.content.*;
import android.graphics.*;
import android.media.ExifInterface;
import android.net.Uri;
import android.os.Build;
import android.util.Base64;
import org.json.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.util.*;
import java.util.zip.*;

/** User-consented content uploads to a PUBLIC GitHub repository.
 * Requires Contents: READ/WRITE and Actions: READ/WRITE; token is Android Keystore-protected.
 * All requests go to api.github.com; only PNG/JPEG selected by the user are read.
 */
public final class PersonalUploadClient {
    private static final int MAX_IMAGE=1_400_000;
    private static final int MAX_STORYBOARD=36_000;
    private static final SecureRandom RANDOM=new SecureRandom();
    private final String token;
    public PersonalUploadClient(String token){this.token=token;}

    public static String requestId(){
        byte[] b=new byte[16];RANDOM.nextBytes(b);
        StringBuilder out=new StringBuilder();
        for(byte v:b)out.append(String.format(Locale.ROOT,"%02x",v&255));
        return out.toString();
    }
    public static boolean validId(String id){return GitHubClient.validId(id);}
    private static String read(InputStream src,int max)throws IOException {
        try(InputStream in=src;ByteArrayOutputStream out=new ByteArrayOutputStream()){
            byte[] buffer=new byte[8192];int n;
            while((n=in.read(buffer))!=-1){
                if(out.size()+n>max)throw new IOException("Respuesta demasiado grande.");
                out.write(buffer,0,n);
            }
            return out.toString("UTF-8");
        }
    }
    private HttpURLConnection connection(String path,String method)throws IOException {
        if(token==null||token.isEmpty())throw new IOException("Conecta GitHub en Ajustes.");
        URL url=new URL("https://api.github.com/repos/"+GitHubClient.REPO+path);
        HttpURLConnection c=(HttpURLConnection)url.openConnection();
        c.setRequestMethod(method);
        c.setInstanceFollowRedirects(false);
        c.setConnectTimeout(15000);c.setReadTimeout(60000);
        c.setRequestProperty("Authorization","Bearer "+token);
        c.setRequestProperty("Accept","application/vnd.github+json");
        c.setRequestProperty("X-GitHub-Api-Version","2022-11-28");
        c.setRequestProperty("User-Agent","AutoStudio-Custom-Android/0.7");
        return c;
    }
    private static String blobSha(byte[] bytes)throws Exception {
        MessageDigest sha=MessageDigest.getInstance("SHA-1");
        sha.update(("blob "+bytes.length+"\0").getBytes(StandardCharsets.UTF_8));
        sha.update(bytes);
        StringBuilder text=new StringBuilder();
        for(byte b:sha.digest())text.append(String.format(Locale.ROOT,"%02x",b&255));
        return text.toString();
    }
    private static String sha256(byte[] bytes)throws Exception {
        MessageDigest md=MessageDigest.getInstance("SHA-256");
        md.update(bytes);
        StringBuilder text=new StringBuilder();
        for(byte b:md.digest())text.append(String.format(Locale.ROOT,"%02x",b&255));
        return text.toString();
    }
    private static void checkName(String id,String file)throws IOException {
        if(!validId(id)||
          !(file.matches("imagen-(0[1-9]|1[0-2])\\.jpg")||file.equals("storyboard.json")))
            throw new IOException("Ruta no permitida.");
    }
    private void put(String id,String file,byte[] data)throws Exception {
        checkName(id,file);
        if(data.length==0||data.length>(file.equals("storyboard.json")?MAX_STORYBOARD:MAX_IMAGE))
            throw new IOException("Archivo excesivo.");
        String path="/contents/requests/"+id+"/"+file;
        HttpURLConnection check=connection(path+"?ref=main","GET");
        try {
            int status=check.getResponseCode();
            if(status==200){
                JSONObject existing=new JSONObject(read(check.getInputStream(),128*1024));
                if(blobSha(data).equals(existing.optString("sha")))return;
                throw new IOException("El archivo remoto tiene otro contenido. Se ha bloqueado su sustitución.");
            }
            if(status!=404)throw new IOException("GitHub: fallo al comprobar archivo ("+status+").");
        }finally{check.disconnect();}
        JSONObject body=new JSONObject();
        body.put("message","AutoStudio personal request "+id+" / "+file);
        body.put("branch","main");
        body.put("content",Base64.encodeToString(data,Base64.NO_WRAP));
        HttpURLConnection c=connection(path,"PUT");
        try{
            c.setDoOutput(true);
            c.setRequestProperty("Content-Type","application/json; charset=utf-8");
            byte[] payload=body.toString().getBytes(StandardCharsets.UTF_8);
            try(OutputStream stream=c.getOutputStream()){stream.write(payload);}
            int status=c.getResponseCode();
            if(status!=201)throw new IOException(
                status==403?"GitHub necesita permiso Contents: lectura y escritura para esta función.":
                "No se pudo guardar el archivo en GitHub ("+status+").");
        }finally{c.disconnect();}
    }
    private static int sampleSize(int w,int h){
        int sample=1;
        while(Math.max(w/sample,h/sample)>1800)sample*=2;
        return sample;
    }
    public static byte[] jpeg(Context context,Uri selected)throws Exception {
        if(selected==null||!"content".equalsIgnoreCase(selected.getScheme()))
            throw new IOException("Selecciona imágenes desde la galería.");
        ContentResolver resolver=context.getContentResolver();
        BitmapFactory.Options info=new BitmapFactory.Options();
        info.inJustDecodeBounds=true;
        try(InputStream in=resolver.openInputStream(selected)){
            if(in==null)throw new IOException("Imagen inaccesible.");
            BitmapFactory.decodeStream(in,null,info);
        }
        if(info.outWidth<400||info.outHeight<400||
            (long)info.outWidth*info.outHeight>65_000_000L)
            throw new IOException("Imagen inválida o demasiado pequeña.");
        BitmapFactory.Options opts=new BitmapFactory.Options();
        opts.inSampleSize=sampleSize(info.outWidth,info.outHeight);
        Bitmap bitmap;
        try(InputStream in=resolver.openInputStream(selected)){
            bitmap=BitmapFactory.decodeStream(in,null,opts);
        }
        if(bitmap==null)throw new IOException("No se pudo abrir la imagen.");
        try{
            int rotation=0;
            try(InputStream in=resolver.openInputStream(selected)){
                if(in!=null){
                    ExifInterface exif=new ExifInterface(in);
                    int orientation=exif.getAttributeInt(ExifInterface.TAG_ORIENTATION,ExifInterface.ORIENTATION_NORMAL);
                    if(orientation==ExifInterface.ORIENTATION_ROTATE_90)rotation=90;
                    if(orientation==ExifInterface.ORIENTATION_ROTATE_180)rotation=180;
                    if(orientation==ExifInterface.ORIENTATION_ROTATE_270)rotation=270;
                }
            }catch(Exception ignored){/* Some documents omit EXIF. */}
            if(rotation!=0){
                Matrix matrix=new Matrix();matrix.postRotate(rotation);
                Bitmap updated=Bitmap.createBitmap(bitmap,0,0,bitmap.getWidth(),bitmap.getHeight(),matrix,true);
                bitmap.recycle();bitmap=updated;
            }
            if(bitmap.getWidth()<400||bitmap.getHeight()<500)
                throw new IOException("Imagen demasiado pequeña para un Short.");
            int max=Math.max(bitmap.getWidth(),bitmap.getHeight());
            if(max>1600){
                float factor=1600f/max;
                Bitmap updated=Bitmap.createScaledBitmap(bitmap,
                    Math.round(bitmap.getWidth()*factor),Math.round(bitmap.getHeight()*factor),true);
                bitmap.recycle();bitmap=updated;
            }
            for(int quality:new int[]{88,80,70,60}){
                ByteArrayOutputStream out=new ByteArrayOutputStream();
                if(!bitmap.compress(Bitmap.CompressFormat.JPEG,quality,out))
                    throw new IOException("Error de compresión.");
                byte[] encoded=out.toByteArray();
                if(encoded.length<=MAX_IMAGE)return encoded;
            }
            throw new IOException("Imagen demasiado compleja para este laboratorio.");
        }finally{bitmap.recycle();}
    }
    public interface Progress {void update(String message);}
    public String submit(Context context,String title,List<String> lines,List<Uri> images,Progress progress)throws Exception {
        if(!validText(title,8,110)||lines==null||images==null||
           lines.size()!=images.size()||lines.size()<2||lines.size()>12)
            throw new IOException("Necesitamos un título, de 2 a 12 párrafos y una imagen por párrafo.");
        String id=requestId();
        JSONArray scenes=new JSONArray();
        Set<String> hashes=new HashSet<>();
        for(int i=0;i<images.size();i++){
            String text=lines.get(i).trim();
            if(!validText(text,16,450))throw new IOException("Comprueba el texto de la escena "+(i+1)+".");
            progress.update("Preparando imagen "+(i+1)+" de "+images.size());
            byte[] encoded=jpeg(context,images.get(i));
            String digest=sha256(encoded);
            if(!hashes.add(digest))throw new IOException("Hay imágenes repetidas. Deben ser distintas.");
            String filename=String.format(Locale.ROOT,"imagen-%02d.jpg",i+1);
            put(id,filename,encoded);
            JSONObject scene=new JSONObject()
                .put("image",filename).put("image_sha256",digest)
                .put("narration",text).put("source_type","illustration")
                .put("rights",new JSONObject().put("license","original_user"));
            scenes.put(scene);
            progress.update("Subida imagen "+(i+1)+" de "+images.size());
        }
        JSONObject request=new JSONObject().put("schema",3).put("request_id",id)
            .put("title",title.trim()).put("format","short").put("language","es")
            .put("editorial_approved",false)
            .put("youtube",new JSONObject().put("enabled",false))
            .put("scenes",scenes);
        put(id,"storyboard.json",request.toString().getBytes(StandardCharsets.UTF_8));
        progress.update("Iniciando vídeo con Álex…");
        new GitHubClient(token).dispatchCustom(id);
        return id;
    }
    private static boolean validText(String text,int min,int max){
        if(text==null||text.trim().length()<min||text.trim().length()>max)return false;
        for(int i=0;i<text.length();i++){
            char c=text.charAt(i);
            if(c<32)return false;
        }
        return true;
    }
}
