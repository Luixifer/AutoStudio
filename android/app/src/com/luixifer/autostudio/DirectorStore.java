package com.luixifer.autostudio;

import android.content.*;
import android.net.Uri;
import android.util.AtomicFile;
import org.json.*;
import java.io.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.zip.*;

/** Independent Director files: never reads or rewrites previous app profiles. */
public final class DirectorStore {
    public static final long MAX=200L*1024*1024;
    private final Context context;public final File root;
    public DirectorStore(Context c){context=c.getApplicationContext();root=new File(c.getFilesDir(),"director-projects");root.mkdirs();}
    public static String id(){return UUID.randomUUID().toString().replace("-","");}
    public File folder(String id)throws Exception{if(!id.matches("[a-f0-9]{32}"))throw new IOException("Proyecto no válido");File f=new File(root,id);f.mkdirs();return f;}
    public synchronized void save(String id,JSONObject p)throws Exception{write(new File(folder(id),"project.json"),p);}
    public JSONObject load(String id)throws Exception{return read(new File(folder(id),"project.json"));}
    public static JSONObject read(File f)throws Exception{AtomicFile a=new AtomicFile(f);try(InputStream in=a.openRead()){return new JSONObject(text(in,2_000_000));}}
    public static String text(InputStream in,int max)throws Exception{ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1){if(out.size()+n>max)throw new IOException("Texto demasiado grande");out.write(b,0,n);}return out.toString("UTF-8");}
    public static void write(File f,JSONObject p)throws Exception{AtomicFile a=new AtomicFile(f);FileOutputStream out=null;try{out=a.startWrite();out.write(p.toString(2).getBytes("UTF-8"));a.finishWrite(out);}catch(Exception e){if(out!=null)a.failWrite(out);throw e;}}
    public String create(String title)throws Exception{String id=id();JSONObject p=new JSONObject().put("schema","autostudio-director/1").put("title",title).put("format","horizontal").put("fps",30).put("youtube_enabled",false).put("voice",new JSONObject().put("mode","kokoro").put("voice","em_alex")).put("chapters",new JSONArray().put(new JSONObject().put("id","capitulo-1").put("title","Capítulo 1").put("scenes",new JSONArray())));save(id,p);return id;}
    public List<String> projects(){File[] files=root.listFiles();List<String> result=new ArrayList<>();if(files!=null)for(File f:files)if(f.isDirectory()&&f.getName().matches("[a-f0-9]{32}")&&new File(f,"project.json").isFile())result.add(f.getName());Collections.sort(result);return result;}
    public static JSONObject ownRights()throws Exception{return new JSONObject().put("license","original_user").put("credit","Material aportado por el usuario; titularidad declarada, no verificada por AutoStudio");}
    public String importFile(String id,Uri uri,String role)throws Exception{
        String ext;
        try(InputStream stream=context.getContentResolver().openInputStream(uri)){if(stream==null)throw new IOException("Recurso no accesible");byte[] h=new byte[32];int n=0,k;while(n<h.length&&(k=stream.read(h,n,h.length-n))>0)n+=k;ext=DirectorMediaFormat.detect(h,n);}
        if(ext==null)throw new IOException("Formato real no admitido. Usa JPG, PNG, WebP, MP4, WAV o MP3.");
        if(role.equals("visual")&&(ext.equals("wav")||ext.equals("mp3"))||!role.equals("visual")&&!(ext.equals("wav")||ext.equals("mp3")))throw new IOException("Tipo de recurso incorrecto");
        File media=new File(folder(id),"media");media.mkdirs();File target=new File(media,id()+"."+ext),temp=new File(media,target.getName()+".part");
        try(InputStream in=context.getContentResolver().openInputStream(uri);OutputStream out=new FileOutputStream(temp)){if(in==null)throw new IOException("No se puede abrir el recurso");byte[] b=new byte[65536];int n;long total=0;while((n=in.read(b))!=-1){total+=n;if(total>MAX)throw new IOException("El recurso supera 200 MiB");out.write(b,0,n);}if(total==0)throw new IOException("Recurso vacío");}catch(Exception e){temp.delete();throw e;}
        if(!temp.renameTo(target))throw new IOException("No se pudo guardar el recurso");return "media/"+target.getName();
    }
    public static void compileQuick(JSONObject project)throws Exception{
        JSONObject quick=project.getJSONObject("_quick");JSONArray images=quick.getJSONArray("images");
        List<String> parts=DirectorQuickPlan.split(quick.optString("text"),images.length());
        JSONArray chapters=new JSONArray(),scenes=null;
        for(int i=0;i<parts.size();i++){
            if(i%30==0){scenes=new JSONArray();chapters.put(new JSONObject().put("id","quick-c-"+(i/30)).put("title","Parte "+(i/30+1)).put("scenes",scenes));}
            String path=images.getString(DirectorQuickPlan.imageFor(i,parts.size(),images.length()));
            scenes.put(new JSONObject().put("id","quick-s-"+i).put("narration",parts.get(i)).put("media",new JSONObject().put("kind","image").put("path",path).put("fit","contain").put("source_audio",false).put("rights",ownRights())).put("camera",new JSONObject().put("movement",i%2==0?"zoom_in":"zoom_out")).put("transition",new JSONObject().put("type","dissolve").put("seconds",.4)));
        }
        project.put("chapters",chapters);
    }
    public static JSONArray parseScript(String text)throws Exception{
        if(text.length()>100000)throw new IOException("Guion demasiado grande; divide el documental");
        JSONArray chapters=new JSONArray(),scenes=new JSONArray();JSONObject chapter=new JSONObject().put("id","c-"+id()).put("title","Capítulo 1").put("scenes",scenes);chapters.put(chapter);
        for(String part:text.replace("\r","").replaceAll("(?m)^(#+[^\\n]*)$","\n\n$1\n\n").split("\\n\\s*\\n")){
            String line=part.trim();if(line.isEmpty())continue;
            if(line.startsWith("#")){String title=line.replaceFirst("^#+\\s*","");if(scenes.length()==0){chapter.put("title",title);}else{scenes=new JSONArray();chapter=new JSONObject().put("id","c-"+id()).put("title",title).put("scenes",scenes);chapters.put(chapter);}continue;}
            if(line.length()>6000)throw new IOException("Párrafo demasiado largo. Separa las escenas con líneas en blanco.");
            if(scenes.length()==30){scenes=new JSONArray();chapter=new JSONObject().put("id","c-"+id()).put("title","Continuación").put("scenes",scenes);chapters.put(chapter);}
            scenes.put(new JSONObject().put("id","s-"+id()).put("narration",line).put("transition",new JSONObject().put("type","dissolve").put("seconds",.4)));
        }
        if(chapters.length()>24)throw new IOException("Demasiados capítulos");return chapters;
    }
    private void collect(Object value,Set<String> paths)throws Exception{
        if(value instanceof JSONObject){JSONObject o=(JSONObject)value;if(o.has("path"))paths.add(o.getString("path"));Iterator<String> keys=o.keys();while(keys.hasNext())collect(o.get(keys.next()),paths);}else if(value instanceof JSONArray){JSONArray a=(JSONArray)value;for(int i=0;i<a.length();i++)collect(a.get(i),paths);}
    }
    public File bundle(String id)throws Exception{
        JSONObject p=load(id);JSONArray chapters=p.getJSONArray("chapters");int count=0;
        for(int c=0;c<chapters.length();c++){JSONArray scenes=chapters.getJSONObject(c).getJSONArray("scenes");for(int i=0;i<scenes.length();i++){JSONObject s=scenes.getJSONObject(i);count++;if(!s.has("media")||s.optString("narration").trim().isEmpty())throw new IOException("Falta imagen, vídeo o narración en una escena");}}
        if(count==0)throw new IOException("Importa o escribe un guion antes de generar");
        Set<String> paths=new TreeSet<>();collect(p,paths);File dir=folder(id),target=new File(dir,"project.zip"),temp=new File(dir,"project.zip.part");long total=0;
        try(ZipOutputStream zip=new ZipOutputStream(new FileOutputStream(temp))){zip.setLevel(0);zip.putNextEntry(new ZipEntry("project.json"));zip.write(p.toString(2).getBytes("UTF-8"));zip.closeEntry();for(String path:paths){File f=new File(dir,path);if(!path.startsWith("media/")||!f.getCanonicalPath().startsWith(dir.getCanonicalPath()+File.separator)||!f.isFile())throw new IOException("Recurso fuera del proyecto");total+=f.length();if(total>MAX-1024*1024)throw new IOException("Paquete superior a 199 MiB. Divide el proyecto por capítulos.");zip.putNextEntry(new ZipEntry(path));try(InputStream in=new FileInputStream(f)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)zip.write(b,0,n);}zip.closeEntry();}}catch(Exception e){temp.delete();throw e;}
        if(target.exists()&&!target.delete())throw new IOException("No se pudo reemplazar el paquete temporal");if(!temp.renameTo(target))throw new IOException("No se pudo guardar el paquete");return target;
    }
    public String restore(Uri uri)throws Exception{
        String id=id();File stage=new File(root,".import-"+id);stage.mkdirs();long total=0;int count=0;Set<String> names=new HashSet<>();
        try(InputStream stream=context.getContentResolver().openInputStream(uri);ZipInputStream zip=new ZipInputStream(stream)){
            ZipEntry entry;while((entry=zip.getNextEntry())!=null){String name=entry.getName();if(++count>3000||!names.add(name)||name.contains("\\")||name.contains(":")||name.startsWith("/")||Arrays.asList(name.split("/")).contains("..")||!(name.equals("project.json")||name.startsWith("media/")))throw new IOException("ZIP no seguro");
                File target=new File(stage,name);if(!target.getCanonicalPath().startsWith(stage.getCanonicalPath()+File.separator))throw new IOException("Ruta fuera del proyecto");if(entry.isDirectory()){target.mkdirs();continue;}target.getParentFile().mkdirs();try(OutputStream out=new FileOutputStream(target)){byte[] b=new byte[65536];int n;while((n=zip.read(b))!=-1){total+=n;if(total>MAX)throw new IOException("Proyecto superior a 200 MiB");out.write(b,0,n);}}zip.closeEntry();}
        }
        JSONObject p=read(new File(stage,"project.json"));if(!p.optString("schema").equals("autostudio-director/1")||p.optBoolean("youtube_enabled",true))throw new IOException("Contrato no compatible");
        File target=new File(root,id);if(!stage.renameTo(target))throw new IOException("No se pudo confirmar la restauración");return id;
    }
    public static String sha(File f)throws Exception{MessageDigest md=MessageDigest.getInstance("SHA-256");try(InputStream in=new FileInputStream(f)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)md.update(b,0,n);}StringBuilder out=new StringBuilder();for(byte b:md.digest())out.append(String.format(java.util.Locale.ROOT,"%02x",b&255));return out.toString();}
}
