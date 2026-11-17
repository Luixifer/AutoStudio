package com.luixifer.autostudio;
import android.content.*;
import android.security.keystore.*;
import android.util.Base64;
import java.security.*;
import javax.crypto.*;
import javax.crypto.spec.GCMParameterSpec;
import java.nio.charset.StandardCharsets;

/** Only device-encrypted runtime credentials. No token/client secret is bundled. */
public final class CredentialStore {
    private static final String ALIAS="autostudio.github.v1",PREFS="private_connection";
    private final Context context;
    public CredentialStore(Context c){context=c.getApplicationContext();}
    private KeyStore store() throws Exception{KeyStore s=KeyStore.getInstance("AndroidKeyStore");s.load(null);return s;}
    public void save(String token) throws Exception{
        if(!TokenFormat.acceptable(token))throw new IllegalArgumentException("La credencial no tiene un formato válido.");
        KeyStore s=store();
        if(!s.containsAlias(ALIAS)){KeyGenerator k=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore");k.init(new KeyGenParameterSpec.Builder(ALIAS,KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT).setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).setRandomizedEncryptionRequired(true).build());k.generateKey();}
        Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");cipher.init(Cipher.ENCRYPT_MODE,(SecretKey)s.getKey(ALIAS,null));
        String value=Base64.encodeToString(cipher.doFinal(token.getBytes(StandardCharsets.UTF_8)),Base64.NO_WRAP),iv=Base64.encodeToString(cipher.getIV(),Base64.NO_WRAP);
        if(!context.getSharedPreferences(PREFS,0).edit().putString("ciphertext",value).putString("iv",iv).commit())throw new IllegalStateException("No se pudo guardar la conexión cifrada.");
    }
    public String load() throws Exception{
        SharedPreferences p=context.getSharedPreferences(PREFS,0);String data=p.getString("ciphertext",null);if(data==null)return null;
        KeyStore s=store();if(!s.containsAlias(ALIAS))throw new IllegalStateException("La conexión cifrada no se puede recuperar. Vuelve a conectar GitHub.");
        Cipher c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.DECRYPT_MODE,(SecretKey)s.getKey(ALIAS,null),new GCMParameterSpec(128,Base64.decode(p.getString("iv",""),Base64.NO_WRAP)));
        return new String(c.doFinal(Base64.decode(data,Base64.NO_WRAP)),StandardCharsets.UTF_8);
    }
    public boolean connected(){try{return load()!=null;}catch(Exception e){return false;}}
    public void clear() throws Exception{context.getSharedPreferences(PREFS,0).edit().clear().commit();KeyStore s=store();if(s.containsAlias(ALIAS))s.deleteEntry(ALIAS);}
}
