package com.luixifer.autostudio;
import org.json.*;
import java.io.*;
import java.net.*;

/** Official GitHub APIs only. Tokens never follow asset redirects. */
public final class DirectorGitHub {
 public static final String REF="codex/autostudio-director",REPO="Luixifer/AutoStudio";
 public static final class ApiFailure extends IOException {public final int status;ApiFailure(int value){super("GitHub HTTP "+value+". Revisa permisos, conexión y diagnóstico de Actions.");status=value;}}
 private final String token;
 public DirectorGitHub(String token)throws IOException{if(!TokenFormat.acceptable(token))throw new IOException("Conecta GitHub en Ajustes. Director requiere Actions: lectura/escritura y Contents: lectura/escritura.");this.token=token;}
 private HttpURLConnection open(String url,boolean auth)throws Exception{
  URL u=new URL(url);String h=u.getHost();if(!u.getProtocol().equals("https")||u.getPort()!=-1||u.getUserInfo()!=null)throw new IOException("Destino no permitido");
  if(auth&&!(h.equals("api.github.com")||h.equals("uploads.github.com")))throw new IOException("No se envían credenciales a ese servidor");
  if(!auth&&!(h.equals("release-assets.githubusercontent.com")||h.endsWith(".blob.core.windows.net")))throw new IOException("Descarga redirigida a un servidor no autorizado");
  HttpURLConnection c=(HttpURLConnection)u.openConnection();c.setConnectTimeout(30000);c.setReadTimeout(120000);c.setInstanceFollowRedirects(false);c.setRequestProperty("User-Agent","AutoStudio-Director/0.1");c.setRequestProperty("Accept","application/vnd.github+json");c.setRequestProperty("X-GitHub-Api-Version","2022-11-28");if(auth)c.setRequestProperty("Authorization","Bearer "+token);return c;
 }
 private JSONObject api(String path,String method,JSONObject body)throws Exception{
  HttpURLConnection c=open("https://api.github.com/repos/"+REPO+path,true);try{c.setRequestMethod(method);if(body!=null){c.setDoOutput(true);c.setRequestProperty("Content-Type","application/json");try(OutputStream out=c.getOutputStream()){out.write(body.toString().getBytes("UTF-8"));}}int code=c.getResponseCode();if(code==204)return new JSONObject();if(code!=200&&code!=201)throw new ApiFailure(code);try(InputStream in=c.getInputStream()){String value=DirectorStore.text(in,2_000_000);return value.trim().startsWith("[")?new JSONObject().put("items",new JSONArray(value)):new JSONObject(value);}}finally{c.disconnect();}
 }
 public JSONObject release(String id)throws Exception{if(!GitHubClient.validId(id))throw new IOException("Solicitud inválida");try{return api("/releases/tags/director-"+id,"GET",null);}catch(ApiFailure e){if(e.status!=404)throw e;}for(int page=1;page<=3;page++){JSONArray items=api("/releases?per_page=100&page="+page,"GET",null).getJSONArray("items");for(int i=0;i<items.length();i++){JSONObject r=items.getJSONObject(i);if(r.optString("tag_name").equals("director-"+id)&&r.optBoolean("draft"))return r;}if(items.length()<100)break;}throw new IOException("No se encuentra el borrador de esta solicitud. Revisa subida y permisos.");}
 public JSONObject start(File bundle,String id)throws Exception{
  String sha=DirectorStore.sha(bundle);JSONObject intent=new JSONObject().put("autostudio_director",1).put("request_id",id).put("bundle_sha256",sha).put("source_ref",REF);
  JSONObject r=api("/releases","POST",new JSONObject().put("tag_name","director-"+id).put("target_commitish",REF).put("name","Director · revisión "+id.substring(0,8)).put("draft",true).put("prerelease",true).put("body",intent.toString()));
  long rid=r.getLong("id");HttpURLConnection c=open("https://uploads.github.com/repos/"+REPO+"/releases/"+rid+"/assets?name=project.zip",true);
  try{c.setRequestMethod("POST");c.setDoOutput(true);c.setRequestProperty("Content-Type","application/zip");c.setFixedLengthStreamingMode(bundle.length());try(InputStream in=new FileInputStream(bundle);OutputStream out=c.getOutputStream()){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)out.write(b,0,n);}if(c.getResponseCode()!=201)throw new IOException("Subida interrumpida. Conserva la solicitud; no se vuelve a enviar automáticamente.");}finally{c.disconnect();}
  api("/actions/workflows/personal-custom.yml/dispatches","POST",new JSONObject().put("ref",REF).put("inputs",new JSONObject().put("request_id",id)));return r;
 }
 private InputStream assetStream(long id)throws Exception{
  HttpURLConnection c=open("https://api.github.com/repos/"+REPO+"/releases/assets/"+id,true);c.setRequestProperty("Accept","application/octet-stream");int code=c.getResponseCode();
  if(code>=300&&code<=308){String target=c.getHeaderField("Location");c.disconnect();c=open(target,false);code=c.getResponseCode();}
  if(code!=200){c.disconnect();throw new IOException("No se pudo descargar el adjunto: HTTP "+code);}
  final HttpURLConnection connection=c;return new FilterInputStream(c.getInputStream()){@Override public void close()throws IOException{try{super.close();}finally{connection.disconnect();}}};
 }
 public JSONObject result(JSONObject r)throws Exception{JSONArray assets=r.getJSONArray("assets");for(int i=0;i<assets.length();i++){JSONObject a=assets.getJSONObject(i);if(a.getString("name").equals("result.json"))try(InputStream in=assetStream(a.getLong("id"))){return new JSONObject(DirectorStore.text(in,200_000));}}return null;}
 public void download(JSONObject r,JSONObject result,File target)throws Exception{
  if(!result.getString("status").equals("completed"))throw new IOException("El documental no se ha completado");JSONArray assets=r.getJSONArray("assets");JSONObject asset=null;for(int i=0;i<assets.length();i++){JSONObject a=assets.getJSONObject(i);if(a.getLong("id")==result.getLong("asset_id")&&a.getString("name").equals("documental-REVISION.mp4"))asset=a;}
  if(asset==null||asset.getLong("size")!=result.getLong("bytes")||asset.getLong("size")>=2L*1024*1024*1024)throw new IOException("Resultado no verificable");
  if(target.isFile()&&target.length()==asset.getLong("size")&&DirectorStore.sha(target).equals(result.getString("sha256")))return;
  if(target.getParentFile().getUsableSpace()<asset.getLong("size")+100L*1024*1024)throw new IOException("No hay espacio libre suficiente en el móvil");
  File temp=new File(target.getParentFile(),target.getName()+".part");long total=0;
  try(InputStream in=assetStream(asset.getLong("id"));OutputStream out=new FileOutputStream(temp)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1){total+=n;if(total>asset.getLong("size"))throw new IOException("Descarga demasiado grande");out.write(b,0,n);}}
  catch(Exception e){temp.delete();throw e;}
  if(total!=asset.getLong("size")||!DirectorStore.sha(temp).equals(result.getString("sha256"))){temp.delete();throw new IOException("Descarga con SHA-256 incorrecto");}
  if(target.exists()&&!target.delete())throw new IOException("No se puede reemplazar la descarga local");if(!temp.renameTo(target))throw new IOException("No se pudo confirmar la descarga");
 }
}
