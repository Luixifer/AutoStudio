package com.luixifer.autostudio;
import android.app.*;
import android.os.*;
import android.text.InputType;
import android.widget.*;
import java.util.concurrent.atomic.AtomicBoolean;

/** Optional research probe. Not a video generator or an editorial approval step. */
public final class ResearchActivity extends Activity {
    private EditText topic;
    private TextView status;
    private Button submit;
    private final AtomicBoolean sending = new AtomicBoolean(false);

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        LinearLayout body = Ui.scroll(this, Ui.root(this, "Investigar un tema"));
        Ui.para(body, "Prueba experimental · AutoStudio 0.4. Investiga cualquier tema usando fuentes públicas. "
            + "Prepara un esquema de seis escenas, no un vídeo ni un guion científico aprobado.");
        LinearLayout card = Ui.card(body);
        card.addView(Ui.text(this, "¿Qué quieres investigar?", 20, true));
        topic = new EditText(this);
        topic.setId(1031);
        topic.setHint("Por ejemplo: ¿Por qué la Luna muestra siempre la misma cara?");
        topic.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        topic.setSingleLine(false);
        topic.setMaxLines(4);
        card.addView(topic, new LinearLayout.LayoutParams(-1, Ui.dp(this, 110)));
        submit = Ui.button(card, "Investigar tema", 1032, true);
        status = Ui.para(card, "El título y las fuentes de la investigación serán públicos en GitHub. No introduzcas datos privados.");
        submit.setOnClickListener(v -> submitTopic());
        Ui.button(body, "Ver investigaciones en GitHub", 1033, false)
          .setOnClickListener(v -> Ui.browser(this,
            "https://github.com/" + GitHubClient.REPO + "/actions/workflows/investigar-tema.yml"));
        Ui.button(body, "Volver", 1034, false).setOnClickListener(v -> finish());
    }

    private void submitTopic() {
        if (sending.get()) return;
        String requested = topic.getText().toString().trim();
        if (requested.length() < 3 || requested.length() > 160
            || requested.matches("(?s).*[\\p{Cntrl}].*")) {
            Ui.error(this, "Escribe un tema de 3 a 160 caracteres sin saltos de línea.");
            return;
        }
        if (!new CredentialStore(this).connected()) {
            Ui.error(this, "Primero conecta tu credencial de GitHub en Ajustes.");
            return;
        }
        sending.set(true);
        submit.setEnabled(false);
        status.setText("Enviando la investigación a GitHub…");
        AutoStudioApp.IO.execute(() -> {
            try {
                new GitHubClient(new CredentialStore(getApplicationContext()).load()).dispatchResearch(requested);
                runOnUiThread(() -> {
                    status.setText("Solicitud enviada. Abre «Ver investigaciones en GitHub» y entra en la ejecución más reciente para leer el Summary. No se ha generado ningún vídeo.");
                    sending.set(false);
                    submit.setEnabled(true);
                });
            } catch (Exception error) {
                runOnUiThread(() -> {
                    status.setText("No se pudo confirmar el envío: " + error.getMessage()
                        + ". Antes de repetirlo, comprueba en GitHub si existe una ejecución. "
                        + "No se enviará automáticamente una segunda vez.");
                    sending.set(false);
                    submit.setEnabled(true);
                });
            }
        });
    }
}
