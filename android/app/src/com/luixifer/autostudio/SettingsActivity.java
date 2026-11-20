package com.luixifer.autostudio;
import android.app.*;
import android.os.*;
import android.text.*;
import android.widget.*;
import android.view.WindowManager;
import java.util.concurrent.Executors;

public final class SettingsActivity extends Activity {
    private TextView message;private EditText token;private Button connect;
    @Override public void onCreate(Bundle b){super.onCreate(b);getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);LinearLayout body=Ui.scroll(this,Ui.root(this,"Conexión con GitHub"));
        Ui.para(body,"Repositorio público: Luixifer/AutoStudio\nNo necesitas contratar un servidor ni una API de IA.");
        boolean director=getPackageName().startsWith("com.luixifer.autostudio.director.");String contentPermission=director?"lectura y escritura":"lectura";
        LinearLayout card=Ui.card(body);card.addView(Ui.text(this,"Configuración inicial",20,true));Ui.para(card,"1. Crea en GitHub un token de acceso personal de granularidad fina.\n2. Selecciona solo AutoStudio.\n3. Permisos: Actions → lectura y escritura; Contents → "+contentPermission+".\n4. Elige una caducidad corta y pega la credencial aquí. Nunca la envíes por chat ni la subas al repositorio.");
        Ui.button(card,"Abrir GitHub para crear la credencial",1020,false).setOnClickListener(v->Ui.browser(this,"https://github.com/settings/personal-access-tokens/new?name=AutoStudio%20Android&target_name=Luixifer&expires_in=30&actions=write&contents="+(director?"write":"read")));
        token=new EditText(this);token.setId(Ui.TOKEN);token.setHint("Pega tu credencial de GitHub");token.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);token.setSingleLine(true);token.setAutofillHints(new String[]{});token.setImportantForAutofill(android.view.View.IMPORTANT_FOR_AUTOFILL_NO_EXCLUDE_DESCENDANTS);card.addView(token,new LinearLayout.LayoutParams(-1,Ui.dp(this,62)));
        message=Ui.para(card,"La credencial se cifrará con Android Keystore. No forma parte del APK y se excluye de las copias de seguridad.");message.setId(Ui.CONNECTION);
        connect=Ui.button(card,"Comprobar y guardar conexión",Ui.CONNECT,true);connect.setOnClickListener(v->{String value=token.getText().toString().trim();connect.setEnabled(false);message.setText("Comprobando acceso de lectura al repositorio y al workflow…");AutoStudioApp.IO.execute(()->{try{new GitHubClient(value).verifyConnection();new CredentialStore(this).save(value);runOnUiThread(()->{token.setText("");message.setText("Conexión guardada. El permiso de ejecución se comprobará al generar.");setResult(RESULT_OK);finish();});}catch(Exception e){runOnUiThread(()->{connect.setEnabled(true);message.setText("No se guardó la conexión: "+e.getMessage());});}});});
        Ui.button(body,"Desconectar y borrar credencial",1021,false).setOnClickListener(v->{try{new CredentialStore(this).clear();token.setText("");message.setText("Credencial eliminada de este dispositivo. También puedes revocarla desde GitHub.");}catch(Exception e){Ui.error(this,"No se pudo borrar la conexión.");}});
        Ui.button(body,"Volver",1022,false).setOnClickListener(v->finish());
    }
}
