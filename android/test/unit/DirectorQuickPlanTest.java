import com.luixifer.autostudio.DirectorQuickPlan;
import java.util.*;
public final class DirectorQuickPlanTest {
 static void check(boolean value){if(!value)throw new AssertionError();}
 public static void main(String[] args){
  String text="La luz llega. Esta es otra frase. Una conclusión final.";
  for(int images:new int[]{1,2,3,10}){
   List<String> scenes=DirectorQuickPlan.split(text,images);check(String.join(" ",scenes).equals(text));
   for(int i=0;i<scenes.size();i++){check(!scenes.get(i).isEmpty());int index=DirectorQuickPlan.imageFor(i,scenes.size(),images);check(index>=0&&index<images);}
  }
  String longText=String.join(" ",Collections.nCopies(1501,"palabra"));List<String> longScenes=DirectorQuickPlan.split(longText,1);check(longScenes.size()==16);check(String.join(" ",longScenes).equals(longText));
  for(int bad:new int[]{0,30,31}){try{DirectorQuickPlan.split(text,bad);throw new AssertionError();}catch(IllegalArgumentException expected){}}
  try{DirectorQuickPlan.split("  ",1);throw new AssertionError();}catch(IllegalArgumentException expected){}
  System.out.println("Quick plan: full text, ordering, grouping, bounds and invalid input PASS");
 }
}
