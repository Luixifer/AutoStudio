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
    public static List<JSONObject> allScenes(JSONObject p)throws Exception{
        List<JSONObject> result=new ArrayList<>();JSONArray chapters=p.getJSONArray("chapters");for(int c=0;c<chapters.length();c++){JSONArray scenes=chapters.getJSONObject(c).getJSONArray("scenes");for(int i=0;i<scenes.length();i++)result.add(scenes.getJSONObject(i));}return result;
    }
    public static void prepareParagraphs(JSONObject p,String text)throws Exception{
        List<String> paragraphs=DirectorQuickPlan.paragraphs(text);buildParagraphs(p,paragraphs,null);
    }
    private static void buildParagraphs(JSONObject p,List<String> paragraphs,List<String> ids)throws Exception{JSONArray chapters=new JSONArray(),scenes=null;
        for(int i=0;i<paragraphs.size();i++){
            if(i%30==0){scenes=new JSONArray();chapters.put(new JSONObject().put("id","c-"+id()).put("title","Parte "+(i/30+1)).put("scenes",scenes));}
            scenes.put(new JSONObject().put("id",ids==null?"s-"+id():ids.get(i)).put("narration",paragraphs.get(i)).put("pause_after",.35).put("camera",new JSONObject().put("movement","zoom_in")).put("transition",new JSONObject().put("type","dissolve").put("seconds",.35)));
        }
        p.put("chapters",chapters).put("scene_policy","paragraph/1");if(!p.has("subtitles"))p.put("subtitles",new JSONObject().put("enabled",true).put("style","documentary"));syncQuick(p);
    }
    public static void syncQuick(JSONObject p)throws Exception{
        if(!p.has("_quick"))p.put("_quick",new JSONObject());JSONArray images=new JSONArray();StringBuilder script=new StringBuilder();
        for(JSONObject scene:allScenes(p)){if(script.length()>0)script.append("\n\n");script.append(scene.getString("narration"));images.put(scene.has("media")?scene.getJSONObject("media").optString("path"):"");}
        p.getJSONObject("_quick").put("text",script.toString()).put("images",images).put("confirmed",true);
    }
    public static void moveScene(JSONObject p,int index,int delta)throws Exception{
        List<JSONObject> list=allScenes(p);Collections.swap(list,index,index+delta);JSONArray chapters=p.getJSONArray("chapters");int n=0;for(int c=0;c<chapters.length();c++){JSONArray scenes=chapters.getJSONObject(c).getJSONArray("scenes");for(int i=0;i<scenes.length();i++)scenes.put(i,list.get(n++));}syncQuick(p);
    }
    public static String shaText(String text)throws Exception{byte[] hash=MessageDigest.getInstance("SHA-256").digest(text.getBytes("UTF-8"));StringBuilder s=new StringBuilder();for(byte b:hash)s.append(String.format(java.util.Locale.ROOT,"%02x",b&255));return s.toString();}
    public static void compileQuick(JSONObject p)throws Exception{
        if(!p.optString("scene_policy").equals("paragraph/1"))throw new IOException("Revisa el guion antiguo: el reparto anterior no se convierte automáticamente.");
        int position=0,missing=0;Set<String> ids=new HashSet<>();
        for(JSONObject scene:allScenes(p)){position++;if(!ids.add(scene.getString("id")))throw new IOException("Escenas con identificadores repetidos");if(!scene.has("media")||scene.getJSONObject("media").optString("path").isEmpty())missing++;if(scene.optString("narration").trim().isEmpty())throw new IOException("La escena "+position+" no tiene narración");}
        if(position==0)throw new IOException("Importa el guion primero");if(missing>0)throw new IOException("Hay "+position+" párrafos y faltan "+missing+" recursos. Cada párrafo necesita su imagen o vídeo.");
    }
    public static void prepareScript(JSONObject p,String input)throws Exception{
        if(!input.trim().startsWith("{")){prepareParagraphs(p,input);return;}
        JSONObject obj=new JSONObject(input);JSONArray chapters=obj.optJSONArray("chapters");if(chapters==null)chapters=new JSONArray().put(new JSONObject().put("scenes",obj.getJSONArray("scenes")));
        List<String> text=new ArrayList<>(),ids=new ArrayList<>();Set<String> unique=new HashSet<>();
        for(int c=0;c<chapters.length();c++){JSONArray scenes=chapters.getJSONObject(c).getJSONArray("scenes");for(int i=0;i<scenes.length();i++){JSONObject scene=scenes.getJSONObject(i);String value=scene.optString("narration",scene.optString("text")),id=scene.optString("id","s-"+id());if(value.trim().isEmpty()||value.length()>6000||!id.matches("[a-zA-Z0-9_-]{1,64}")||!unique.add(id))throw new IOException("Texto o ID de escena JSON inválido");text.add(value);ids.add(id);}}
        if(text.isEmpty()||text.size()>720)throw new IOException("Cantidad de escenas JSON no válida");buildParagraphs(p,text,ids);
    }
    public static String scriptText(String input)throws Exception{
        if(!input.trim().startsWith("{"))return input;
        JSONObject obj=new JSONObject(input);JSONArray chapters=obj.optJSONArray("chapters");StringBuilder text=new StringBuilder();
        if(chapters==null)chapters=new JSONArray().put(new JSONObject().put("scenes",obj.getJSONArray("scenes")));
        for(int c=0;c<chapters.length();c++){JSONArray scenes=chapters.getJSONObject(c).getJSONArray("scenes");for(int i=0;i<scenes.length();i++){JSONObject scene=scenes.getJSONObject(i);String narration=scene.optString("narration",scene.optString("text"));if(narration.trim().isEmpty())throw new IOException("Escena JSON sin texto");if(text.length()>0)text.append("\n\n");text.append(narration);}}
        return text.toString();
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
    public void validateBindings(String id,JSONObject p)throws Exception{
        compileQuick(p);Set<String> seen=new HashSet<>();File folder=folder(id);
        for(JSONObject scene:allScenes(p)){JSONObject media=scene.getJSONObject("media");String path=media.getString("path");File file=new File(folder,path);if(!path.startsWith("media/")||!file.getCanonicalPath().startsWith(folder.getCanonicalPath()+File.separator)||!file.isFile())throw new IOException("Recurso ausente en una escena");if(!seen.add(sha(file))&&!media.optBoolean("allow_reuse"))throw new IOException("Hay un recurso repetido entre párrafos. Revisa sus tarjetas antes de generar.");}
    }
    public File bundle(String id)throws Exception{
        JSONObject p=load(id);if(p.optString("scene_policy").equals("paragraph/1"))validateBindings(id,p);JSONArray chapters=p.getJSONArray("chapters");int count=0;
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
