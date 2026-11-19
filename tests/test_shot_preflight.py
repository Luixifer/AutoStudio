"""Story-wide visual shot preflight: fail before FLUX, generic across topics."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import shot_preflight as planner
from scripts import visual_autopilot as auto

STORY={"schema":3,"title":"Tides and clouds","scenes":[
    {"narration":"The Moon's gravity drives Earth's rising ocean tides."},
    {"narration":"Water evaporates from the ocean and rises into the atmosphere."},
    {"narration":"Water vapor condenses into droplets inside moving clouds."}]}

def shot(i,scale,angle,role,subject,action):
    return {"scene":i,"scale":scale,"angle":angle,"role":role,
            "subject":subject,"visible_action":action}

VALID={"shots":[
    shot(1,"wide","overhead","establish","Earth and ocean tides",
         "The ocean shoreline is visible from an orbital distance."),
    shot(2,"medium","side","process","Water above the ocean",
         "Water vapor rises upward from a sea surface."),
    shot(3,"close","frontal","detail","Cloud droplets in atmosphere",
         "Tiny droplets gather as vapor condenses into cloud formations.")]}

def jpeg():
    return (b"\xff\xd8\xff\xc0\x00\x11\x08"
         +(512).to_bytes(2,"big")*2+b"\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00"
         +b"\xff\xd9"+b"\x00"*8)

class ShotPlanTests(unittest.TestCase):
    def test_validates_unique_compositions_and_preserves_scene_order(self):
        result=planner.validate_plan(VALID,STORY)
        self.assertEqual(len(result),3)
        self.assertEqual(result[1]["role"],"process")
        self.assertIn("overhead",planner.shot_context(result[0]))

    def test_repetition_and_wrong_scene_count_fail_before_generation(self):
        duplicate=json.loads(json.dumps(VALID))
        duplicate["shots"][1]["scale"]="wide"
        duplicate["shots"][1]["angle"]="overhead"
        duplicate["shots"][1]["role"]="establish"
        with self.assertRaisesRegex(ValueError,"Repeated"):
            planner.validate_plan(duplicate,STORY)
        with self.assertRaisesRegex(ValueError,"number"):
            planner.validate_plan({"shots":VALID["shots"][:2]},STORY)

    def test_same_visible_action_with_different_camera_metadata_is_rejected(self):
        story={"scenes":[
            {"narration":"A gas giant is surrounded by a glowing cloud of gas."},
            {"narration":"The giant's gas cloud swirls around its atmosphere."}]}
        proposed={"shots":[
            shot(1,"wide","frontal","establish","Gas giant and its atmosphere",
                 "Swirling gas clouds surround a glowing giant planet with turbulent strands."),
            shot(2,"close","side","process","Gas giant's atmosphere",
                 "Turbulent swirling gas clouds surround a glowing giant planet with strands.")]}
        with self.assertRaisesRegex(ValueError,"Near-duplicate visible action"):
            planner.validate_plan(proposed,story)

    def test_repeated_subject_with_new_physical_relationship_is_allowed(self):
        story={"scenes":[
            {"narration":"A gaseous planet is illuminated by its parent star."},
            {"narration":"The gaseous planet travels on an orbit near its parent star."}]}
        proposed={"shots":[
            shot(1,"wide","frontal","establish","Planet and parent star",
                 "A gas planet and bright parent star appear together in a wide view."),
            shot(2,"medium","side","relationship","Planet in orbit",
                 "A side view reveals the curved orbital path between the planet and star.")]}
        self.assertEqual(len(planner.validate_plan(proposed,story)),2)

    def test_parse_code_fence_and_schema_fail_closed(self):
        result=planner.parse_reply("```json\n"+json.dumps(VALID)+"\n```")
        self.assertEqual(len(planner.validate_plan(result,STORY)),3)
        with self.assertRaisesRegex(ValueError,"invalid JSON"):
            planner.parse_reply("Certainly, here are ten shots.")

    def test_abstract_two_word_actions_rejected(self):
        bad=json.loads(json.dumps(VALID))
        bad["shots"][0]["visible_action"]="Orbital period"
        with self.assertRaisesRegex(ValueError,"concrete observable"):
            planner.validate_plan(bad,STORY)
        bad["shots"][0]["visible_action"]="A chart of the orbital period appears beside a planet."
        with self.assertRaisesRegex(ValueError,"Abstract visual shorthand"):
            planner.validate_plan(bad,STORY)

    def test_bounded_plan_repair_before_any_image_generation(self):
        calls=[]
        answers=[{"response":"not JSON"},{"response":json.dumps(VALID)},
                 {"response":json.dumps({"decision":"PASS","issues":[]})}]
        def model(*args):
            calls.append(args)
            return answers.pop(0)
        result=planner.build_plan(STORY,model,"a"*32,"test")
        self.assertEqual(len(result),3)
        self.assertEqual(len(calls),3)
        self.assertIn("PREVIOUS PLAN REJECTED",calls[1][1]["messages"][0]["content"])

    def test_invalid_twice_fails_closed(self):
        calls=[]
        def model(*args):
            calls.append(1)
            return {"response":"{}"}
        with self.assertRaisesRegex(ValueError,"failed preflight twice"):
            planner.build_plan(STORY,model,"a"*32,"test")
        self.assertEqual(len(calls),2)

    def test_build_plan_runs_a_separate_narration_consistency_review(self):
        calls=[]
        def fake_request(model,payload,account,token):
            calls.append((model,payload))
            if len(calls)==1:
                return {"response":json.dumps(VALID)}
            return {"response":json.dumps({"decision":"PASS","issues":[]})}
        result=planner.build_plan(STORY,fake_request,"a"*32,"test")
        self.assertEqual(len(result),3)
        self.assertEqual(len(calls),2)
        self.assertIn("CONTRADICTION reviewer",calls[1][1]["messages"][0]["content"])
        text=calls[0][1]["messages"][0]["content"]
        self.assertIn("The Moon's gravity",text)
        self.assertIn("Water vapor",text)
        self.assertNotIn("KELT-9b",text)

    def test_explicit_gaseous_world_cannot_acquire_hot_surface(self):
        story={"scenes":[
            {"narration":"Es un mundo gaseoso calentado por una estrella cercana."},
            {"narration":"Aquí no hay un suelo de lava, solo una enorme atmósfera de gas."}]}
        shots=[{"scene":1,"subject":"The illuminated planet side",
                "visible_action":"A scorching hot surface glowing under the intense starlight."}]
        with self.assertRaisesRegex(ValueError,"solid ground"):
            planner.check_explicit_story_constraints(story,shots)
        shots[0]["subject"]="The luminous star"
        self.assertTrue(planner.check_explicit_story_constraints(story,shots))

    def test_unsupported_dust_or_galaxy_fails_without_any_model_call(self):
        story={"scenes":[{"narration":"Un planeta enorme compuesto por gas orbita una estrella."}]}
        shot={"scene":1,"subject":"A gas planet",
              "visible_action":"A swirl of dusty gas enveloping the gaseous planet."}
        with self.assertRaisesRegex(ValueError,"dust"):
            planner.check_explicit_story_constraints(story,[shot])
        shot["visible_action"]="The planet appears in a remote galaxy with a blazing star."
        with self.assertRaisesRegex(ValueError,"galaxy"):
            planner.check_explicit_story_constraints(story,[shot])
        shot["visible_action"]="A gas planet orbiting very close to its bright star."
        self.assertTrue(planner.check_explicit_story_constraints(story,[shot]))

    def test_critic_prompt_respects_accurate_paraphrases(self):
        recorded=[]
        def fake(model,payload,account,token):
            recorded.append(payload["messages"][0]["content"])
            return {"response":json.dumps({"decision":"PASS","issues":[]})}
        self.assertTrue(planner.review_story_consistency(
            STORY,planner.validate_plan(VALID,STORY),fake,"a"*32,"test"))
        self.assertIn("translations",recorded[0])
        self.assertIn("supported",recorded[0].lower())
        self.assertIn("Water evaporates",recorded[0])


    def test_critic_accepts_known_nested_cloudflare_envelopes(self):
        for response in (
            {"response":'```json\n{"decision":"PASS","issues":[]}\n```'},
            {"result":{"choices":[{"message":{"content":'{"decision":"PASS","issues":[]}'}}]}},
            {"output":[{"text":'{"decision":"PASS","issues":[]}'}]},
            {"response":'{"decision":" pass ","issues":[]}'},
        ):
            calls=[]
            def fake(*args):
                calls.append(1)
                return response
            self.assertTrue(planner.review_story_consistency(
                STORY,planner.validate_plan(VALID,STORY),fake,"account","token"))
            self.assertEqual(len(calls),1)

    def test_critic_retries_malformed_reply_without_replanning(self):
        replies=[{"response":'{"decision":"PA'},{"response":'{"decision":"PASS","issues":[]}'}]
        calls=[]
        def fake(_model,payload,*_args):
            calls.append(payload["messages"][0]["content"])
            return replies.pop(0)
        self.assertTrue(planner.review_story_consistency(
            STORY,planner.validate_plan(VALID,STORY),fake,"account","token"))
        self.assertEqual(len(calls),2)
        self.assertIn("previous response could not be parsed",calls[1])

    def test_critic_never_turns_missing_or_invalid_content_into_pass(self):
        for bad in ({"response":""}, {"metadata":{"decision":"PASS","issues":[]}},
                    {"response":'{"decision":"PASS","issues":[{"scene":1,"issue":"Contradiction!"}]}'},
                    {"response":'{"decision":"MAYBE","issues":[]}'}):
            calls=[]
            def fake(*args):
                calls.append(1)
                return bad
            with self.assertRaises(ValueError):
                planner.review_story_consistency(
                    STORY,planner.validate_plan(VALID,STORY),fake,"account","token")
            self.assertGreaterEqual(len(calls),1)

    def test_grounding_failure_repairs_entire_shot_list_once(self):
        calls=[]
        answers=[
            {"response":json.dumps(VALID)},
            {"response":json.dumps({"decision":"FAIL","issues":[
                {"scene":1,"issue":"An unsupported physical surface appears in the shot."}]})},
            {"response":json.dumps(VALID)},
            {"response":json.dumps({"decision":"PASS","issues":[]})}]
        def model(*args):
            calls.append(args)
            return answers.pop(0)
        shotlist=planner.build_plan(STORY,model,"a"*32,"test")
        self.assertEqual(len(shotlist),3)
        self.assertEqual(len(calls),4)
        self.assertIn("unsupported physical surface",calls[2][1]["messages"][0]["content"])

    def test_grounding_failure_twice_blocks_all_generation(self):
        calls=[]
        fail={"response":json.dumps({"decision":"FAIL","issues":[
            {"scene":1,"issue":"Unsupported geographic setting for the first scene."}]})}
        outputs=[{"response":json.dumps(VALID)},fail,
                 {"response":json.dumps(VALID)},fail]
        def model(*args):
            calls.append(args)
            return outputs.pop(0)
        with self.assertRaisesRegex(ValueError,"failed preflight twice"):
            planner.build_plan(STORY,model,"a"*32,"test")
        self.assertEqual(len(calls),4)


    def test_semantic_repair_keeps_complete_plan_including_last_scene(self):
        long_story={"title":"General science film","scenes":[
            {"narration":f"Observable effect {i} happens in the ocean and the atmosphere."}
            for i in range(1,11)]}
        original={"shots":[shot(i,["wide","medium","close","extreme_wide","extreme_close"][((i-1)%5)],
              ["side","frontal","low","overhead","high","three_quarter"][((i-1)%6)],
              ["establish","process","detail","contrast","consequence","relationship","transition"][((i-1)%7)],
              f"Ocean atmosphere unique subject number {i}",
              f"Different ocean atmosphere event number {i} visible far beyond a distant galaxy.")
              for i in range(1,11)]}
        self.assertGreater(len(json.dumps(original)),1200)
        corrected=json.loads(json.dumps(original))
        for item in corrected["shots"]:
            item["visible_action"]=item["visible_action"].replace("distant galaxy","ocean atmosphere")
        answers=[{"response":json.dumps(original)},{"response":json.dumps(corrected)},
                 {"response":json.dumps({"decision":"PASS","issues":[]})}]
        prompts=[]
        def fake(_model,payload,*_args):
            prompts.append(payload["messages"][0]["content"])
            return answers.pop(0)
        result=planner.build_plan(long_story,fake,"account","token")
        self.assertEqual(len(result),10)
        self.assertEqual(len(prompts),3)
        self.assertIn('"scene": 10',prompts[1])
        self.assertIn("unsupported galaxy",prompts[1])
        self.assertIn("FULL PREVIOUS PLAN",prompts[1])

    def test_semantic_repair_remains_fail_closed(self):
        bad=json.loads(json.dumps(VALID))
        bad["shots"][0]["visible_action"]="The whole planet lies inside an unsupported distant galaxy."
        responses=[{"response":json.dumps(bad)},{"response":json.dumps(bad)}]
        def fake(*_args):
            return responses.pop(0)
        with self.assertRaisesRegex(ValueError,"failed preflight twice"):
            planner.build_plan(STORY,fake,"account","token")

    def test_invalid_plan_issues_no_flux_requests(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/"story.json"
            path.write_text(json.dumps(STORY))
            flux=[]
            with patch.dict("os.environ",{"CLOUDFLARE_ACCOUNT_ID":"a"*32,
                                       "CLOUDFLARE_API_TOKEN":"test"}):
                with self.assertRaisesRegex(ValueError,"Repeated"):
                    auto.run(path,Path(t)/"out",live=True,max_attempts=1,request_budget=3,
                        shot_planner=lambda *args:planner.validate_plan(
                            {"shots":[dict(item,scale="wide",angle="overhead",role="establish") for item in VALID["shots"]]},STORY),
                        director=lambda *a:"A scientifically plausible image of the Earth and ocean.",
                        generator=lambda *a:flux.append(1))
            self.assertEqual(flux,[])
            report=json.loads((Path(t)/"out"/"visual-supervision-manifest.json").read_text())
            self.assertEqual(report["completed_requests"],0)

    def test_valid_plan_drives_all_scene_prompts_without_extra_flux(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/"story.json"
            path.write_text(json.dumps(STORY))
            prompts=[]
            def director(narration,title,previous,account,token):
                prompts.append(previous)
                return "A scientific exterior view with an accurately depicted ocean and atmospheric layer."
            def vision(image,narration,prompt,account,token):
                return {"decision":"PASS","evidence":"A unique scientific scene of water and atmospheric activity."}
            with patch.dict("os.environ",{"CLOUDFLARE_ACCOUNT_ID":"a"*32,
                                       "CLOUDFLARE_API_TOKEN":"test"}):
                result=auto.run(path,Path(t)/"out",live=True,max_attempts=1,request_budget=3,
                                shot_planner=lambda *a:planner.validate_plan(VALID,STORY),
                                director=director,generator=lambda *a:jpeg(),vision=vision)
            self.assertTrue(result["preflight_validated"])
            # The existing director may also replan a repeated image prompt,
            # so multiple text calls are permitted, never extra FLUX.
            self.assertGreaterEqual(len(prompts),3)
            self.assertTrue(any("overhead" in p for p in prompts))
            self.assertTrue(any("process" in p for p in prompts))
            self.assertTrue(any("detail" in p for p in prompts))
            self.assertEqual(result["completed_requests"],3)

if __name__=="__main__":
    unittest.main()
