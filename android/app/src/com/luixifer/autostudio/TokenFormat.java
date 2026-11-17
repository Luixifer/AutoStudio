package com.luixifer.autostudio;
/** GitHub credentials are opaque. Do not assume a prefix, alphabet or old length. */
public final class TokenFormat {
    public static boolean acceptable(String token){
        if(token==null||token.length()<20||token.length()>8192)return false;
        for(int i=0;i<token.length();i++){char c=token.charAt(i);if(c<=32||c>=127)return false;}
        return true;
    }
    private TokenFormat(){}
}
