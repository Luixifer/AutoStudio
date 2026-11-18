package com.luixifer.autostudio;
import org.json.*;
import java.net.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

/** HTTPS allowlists; authentication is NEVER forwarded to a download host. */
public final class GitHubClient {
    public static final String REPO="Luixifer/AutoStudio",WORKFLOW="produce-short.yml";
    private final String token;
    public GitHubClient(String t){token=t;}
    public static final class ApiError extends IOException {public final int code;public ApiError(int c){super(c==401?"GitHub ha rechazado la credencial. Revisa su vigencia.":c==403?"GitHub ha denegado la operación. Revisa permisos Actions: lectura y escritura y límites de solicitudes.":c==404?"No se encontró el repositorio o el workflow. Revisa la conexión.":c==422?"GitHub no ha aceptado la solicitud de producción.":"GitHub devolvió el estado "+c+". Puedes consultar de nuevo.");code=c;}}
    public static boolean validId(String id){return id!=null&&id.matches("[a-f0-9]{32}");}
    private static HttpURLConnection connection(String url,boolean authenticated,String token) throws Exception{
        URL u=new URL(url);String host=u.getHost();
        if(!u.getProtocol().equals("https")||u.getPort()!=-1||!(authenticated?host.equals("api.github.com"):host.equals("raw.githubusercontent.com")))throw new IOException("Destino de red no autorizado.");
        HttpURLConnection c=(HttpURLConnection)u.openConnection();c.setConnectTimeout(15000);c.setReadTimeout(45000);c.setInstanceFollowRedirects(false);c.setRequestProperty("User-Agent","AutoStudio-Android-Control/0.4");c.setRequestProperty("Cache-Control","no-cache");
        if(authenticated){if(token==null||token.isEmpty())throw new IOException("Conecta GitHub antes de producir.");c.setRequestProperty("Authorization","Bearer "+token);c.setRequestProperty("Accept","application/vnd.github+json");c.setRequestProperty("X-GitHub-Api-Version","2022-11-28");}return c;
    }
    private static String read(InputStream input,int max) throws Exception{try(InputStream in=input;ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1){if(out.size()+n>max)throw new IOException("Respuesta demasiado grande.");out.write(b,0,n);}return out.toString("UTF-8");}}
    private JSONObject api(String path,String method,JSONObject body) throws Exception{
        HttpURLConnection c=connection("https://api.github.com/repos/"+REPO+path,true,token);
        try{c.setRequestMethod(method);if(body!=null){c.setDoOutput(true);c.setRequestProperty("Content-Type","application/json; charset=utf-8");try(OutputStream o=c.getOutputStream()){o.write(body.toString().getBytes(StandardCharsets.UTF_8));}}
            int status=c.getResponseCode();if(status==204)return new JSONObject();if(status!=200)throw new ApiError(status);return new JSONObject(read(c.getInputStream(),2*1024*1024));
        }finally{c.disconnect();}
    }
    public void verifyConnection() throws Exception{JSONObject repo=api("","GET",null);if(repo.optBoolean("private",true))throw new IOException("Esta edición solo produce en el repositorio público previsto; no activa runners de pago.");JSONObject flow=api("/actions/workflows/"+WORKFLOW,"GET",null);if(!flow.optString("state").equals("active"))throw new IOException("El workflow de producción no está activo.");}
    public void dispatch(String id,String topic) throws Exception{if(!validId(id))throw new IOException("Identificador inválido.");JSONObject inputs=new JSONObject().put("request_id",id).put("topic",topic);api("/actions/workflows/"+WORKFLOW+"/dispatches","POST",new JSONObject().put("ref","main").put("inputs",inputs));}
    /** Dispatches one of three reviewed catalogue identifiers; no arbitrary-topic promise. */
    public void dispatchPersonal(String topic) throws Exception {
        if(!("auroras".equals(topic)||"dna".equals(topic)||"volcanoes".equals(topic)))
            throw new IOException("Tema aún no disponible para vídeo: "+topic);
        JSONObject inputs=new JSONObject().put("topic",topic);
        api("/actions/workflows/personal-topic.yml/dispatches","POST",
            new JSONObject().put("ref","main").put("inputs",inputs));
    }
    /** Validated user-script request; actual data was uploaded via Contents API. */
    public void dispatchCustom(String requestId)throws Exception {
        if(!validId(requestId))throw new IOException("Solicitud personal inválida.");
        api("/actions/workflows/personal-custom.yml/dispatches","POST",
            new JSONObject().put("ref","main").put("inputs",
                new JSONObject().put("request_id",requestId)));
    }
    /** Launches the read-only research trial. This does not produce an MP4. */
    public void dispatchResearch(String topic) throws Exception {
        if (topic == null || topic.trim().length() < 3 || topic.trim().length() > 160
            || topic.matches("(?s).*[\\p{Cntrl}].*")) throw new IOException("Tema no válido.");
        JSONObject inputs = new JSONObject().put("topic", topic.trim());
        api("/actions/workflows/investigar-tema.yml/dispatches", "POST",
            new JSONObject().put("ref", "main").put("inputs", inputs));
    }
    public JSONObject getRun(String id) throws Exception{if(id==null||!id.matches("[0-9]{1,20}"))throw new IOException("Ejecución inválida.");return api("/actions/runs/"+id,"GET",null);}
    public JSONObject findRun(String id) throws Exception{
        if(!validId(id))throw new IOException("Identificador inválido.");
        JSONObject response=api("/actions/workflows/"+WORKFLOW+"/runs?event=workflow_dispatch&per_page=50","GET",null);JSONArray runs=response.getJSONArray("workflow_runs");
        for(int i=0;i<runs.length();i++){JSONObject r=runs.getJSONObject(i);if(r.optString("display_title").equals("AutoStudio · control · "+id))return r;}return null;
    }
    public static String base(String id){if(!validId(id))throw new IllegalArgumentException("Identificador inválido.");return "https://raw.githubusercontent.com/"+REPO+"/video-preview/jobs/"+id+"/";}
    public static JSONObject publicJson(String url) throws Exception{HttpURLConnection c=connection(url,false,null);try{int status=c.getResponseCode();if(status==404)return null;if(status!=200)throw new ApiError(status);return new JSONObject(read(c.getInputStream(),512*1024));}finally{c.disconnect();}}
    public JSONObject result(String id,String runId) throws Exception{
        JSONObject result=publicJson(base(id)+"result.json?check="+System.currentTimeMillis());if(result==null)return null;
        if(result.optInt("schema")!=1||!result.optString("request_id").equals(id)||!result.optString("run_id").equals(runId)||!result.optString("repository").equals(REPO))throw new IOException("El resultado no corresponde a esta solicitud. Se ha rechazado.");return result;
    }
    public static String sha256(File file) throws Exception{MessageDigest digest=MessageDigest.getInstance("SHA-256");try(InputStream in=new FileInputStream(file)){byte[] b=new byte[32768];int n;while((n=in.read(b))!=-1)digest.update(b,0,n);}StringBuilder out=new StringBuilder();for(byte b:digest.digest())out.append(String.format(java.util.Locale.ROOT,"%02x",b&255));return out.toString();}
    public static void download(String id,JSONObject info,File destination) throws Exception{
        long size=info.getLong("bytes");String hash=info.getString("sha256");if(size<=0||size>20*1024*1024||!hash.matches("[a-f0-9]{64}"))throw new IOException("El vídeo excede el límite o no tiene un hash válido.");
        destination.getParentFile().mkdirs();if(destination.isFile()&&destination.length()==size&&sha256(destination).equals(hash))return;
        File temp=new File(destination.getPath()+".part");HttpURLConnection c=connection(base(id)+"short_ciencia_demo.mp4",false,null);
        try{if(c.getResponseCode()!=200)throw new IOException("No se pudo descargar el MP4. Vuelve a consultar.");long total=0;
            try(InputStream in=c.getInputStream();FileOutputStream out=new FileOutputStream(temp)){byte[] b=new byte[32768];int n;while((n=in.read(b))!=-1){total+=n;if(total>size)throw new IOException("Tamaño de vídeo inesperado.");out.write(b,0,n);}out.getFD().sync();}
            if(total!=size||!sha256(temp).equals(hash))throw new IOException("El MP4 descargado no coincide con su SHA-256. No se reproducirá.");
            if(destination.exists()&&!destination.delete())throw new IOException("No se puede sustituir la caché local.");if(!temp.renameTo(destination))throw new IOException("No se pudo confirmar la descarga.");
        }finally{c.disconnect();if(temp.exists())temp.delete();}
    }
}
