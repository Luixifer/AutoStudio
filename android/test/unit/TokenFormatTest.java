import com.luixifer.autostudio.TokenFormat;
/** Genuine executable JVM regressions, fake non-secret fixtures only. */
public final class TokenFormatTest {
    private static int checks;
    private static void check(boolean value){checks++;if(!value)throw new AssertionError("Credential format regression "+checks);}
    public static void main(String[] args){
        check(TokenFormat.acceptable("example_personal_access_credential_123456789"));
        check(TokenFormat.acceptable("example.app-token.with-dots_and-dashes.123456789"));
        StringBuilder large=new StringBuilder("example-long-runtime.");for(int i=0;i<1000;i++)large.append("Ab-_");large.append(".signature");
        check(TokenFormat.acceptable(large.toString()));
        check(!TokenFormat.acceptable(null));check(!TokenFormat.acceptable("too-short"));
        check(!TokenFormat.acceptable("example_credential\nwith_newline_123456"));
        check(!TokenFormat.acceptable("example_credential\rwith_return_123456"));
        check(!TokenFormat.acceptable("example_credential with_space_123456"));
        check(!TokenFormat.acceptable("example_credential\twith_tab_123456"));
        check(!TokenFormat.acceptable("example_credential\u007fcontrol_123456"));
        check(!TokenFormat.acceptable("example_credential_é_nonascii_123456"));
        StringBuilder huge=new StringBuilder();for(int i=0;i<8193;i++)huge.append('a');check(!TokenFormat.acceptable(huge.toString()));
        System.out.println("Credential format JVM regressions passed: "+checks);
    }
}
