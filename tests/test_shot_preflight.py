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

    def test_json_extractor_reads_single_wrapped_complete_object(self):
        raw=json.dumps(VALID)
        for response in (raw,"Here is the result:\n"+raw,
                         raw+"\nDone.","JSON follows:\n"+raw+"\nEnd."):
            self.assertEqual(planner.parse_reply(response),VALID)

    def test_json_extractor_rejects_ambiguous_or_truncated_output(self):
        raw=json.dumps(VALID)
        for value in (raw[:-1],raw+"\n"+raw,"[]","No JSON here",
                      '{"shots":[}', '{"shots":[]}\n{"shots":[]}'):
            with self.subTest(value=value[:30]):
                with self.assertRaisesRegex(ValueError,"invalid JSON"):
                    planner.parse_reply(value)

    def test_chunk_invalid_json_retry_is_bounded_and_fail_closed(self):
        story={"scenes":[
            {"narration":f"Wave action {i} moves across the surface of the ocean."}
            for i in range(5)]}
        prompts=[]
        def fake(_model,payload,*_args):
            prompts.append(payload["messages"][0]["content"])
            return {"response":'{"shots":['}
        with self.assertRaisesRegex(ValueError,"Shot batch 1 failed twice"):
            planner.build_plan(story,fake,"account","token")
        self.assertEqual(len(prompts),4)
        self.assertIn("final bounded retry",prompts[1])
        self.assertIn("exactly 2 shots",prompts[1])
        self.assertIn("EXACTLY 1 objects",prompts[2])

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


    def test_semantic_repair_changes_only_offending_scene(self):
        events=["tidal crest","evaporating droplets","condensing mist","wind currents",
                "rolling wavefronts","breaking foam","rising vapor","gathering clouds",
                "falling rainfall","reflected moonlight"]
        story={"title":"Ocean documentary","scenes":[
            {"narration":f"Ocean and atmosphere show {item} from above."}
            for item in events]}
        original={"shots":[shot(i,["wide","medium","close","extreme_wide","extreme_close"][((i-1)%5)],
              ["side","frontal","low","overhead","high","three_quarter"][((i-1)%6)],
              ["establish","process","detail","contrast","consequence","relationship","transition"][((i-1)%7)],
              f"Ocean scene {i} and its atmosphere",
              f"The {events[i-1]} appears above the ocean during a different visible process.")
              for i in range(1,11)]}
        original["shots"][0]["visible_action"]="The tidal crest appears above the ocean in a remote galaxy."
        planner.validate_plan(original,story)
        with self.assertRaisesRegex(ValueError,"unsupported galaxy"):
            planner.check_explicit_story_constraints(story,original["shots"])
        repaired={"subject":"Ocean waves and crest",
                  "visible_action":"A tidal crest rises above the ocean near foaming water."}
        answers=[{"response":json.dumps(original)},{"response":json.dumps(repaired)},
                 {"response":json.dumps({"decision":"PASS","issues":[]})}]
        prompts=[]
        def fake(_model,payload,*_args):
            prompts.append(payload["messages"][0]["content"])
            return answers.pop(0)
        result=planner._build_plan_whole(story,fake,"account","token")
        self.assertEqual(len(result),10)
        self.assertEqual(len(prompts),3)
        self.assertIn("Repair ONE invalid documentary shot",prompts[1])
        self.assertIn("unsupported galaxy",prompts[1])
        self.assertEqual(result[1:],original["shots"][1:])
        self.assertEqual(result[0]["visible_action"],repaired["visible_action"])

    def test_semantic_repair_cannot_approve_unsupported_fact(self):
        story={"scenes":[{"narration":"An ocean tide moves toward the coast."}]}
        first={"shots":[shot(1,"wide","side","establish","Ocean tide",
            "The tide moves toward a coast in a distant galaxy.")]}
        bad_patch={"subject":"Ocean tide","visible_action":
            "The ocean tide continues near a remote galaxy."}
        outputs=[{"response":json.dumps(first)},{"response":json.dumps(bad_patch)}]
        def fake(*_args):
            return outputs.pop(0)
        with self.assertRaisesRegex(ValueError,"failed preflight twice"):
            planner.build_plan(story,fake,"account","token")


    def test_long_story_generates_small_batches_and_keeps_global_order(self):
        details=[
            ("wide","side","establish","Ocean waves","Ocean waves rise along the curved shoreline during a morning tide."),
            ("close","frontal","detail","Cloud droplets","Small droplets collect inside thick clouds above the coastal ocean."),
            ("medium","high","process","Ocean mist","Thin mist rises from warm water into the air overhead."),
            ("extreme_wide","overhead","contrast","Moon and sea","The distant moon hangs above a wide view of the ocean."),
            ("extreme_close","low","consequence","Rainfall","Heavy raindrops fall from a dark cloud onto the sea."),
            ("medium","three_quarter","relationship","Sea and wind","Moving air pushes small wave crests across a broad surface.")
        ]
        story={"title":"Ocean processes","scenes":[{"narration":x[4]} for x in details]}
        batches=[]
        for offset in (0,2,4):
            batches.append({"response":json.dumps({"shots":[
                shot(j+1,*details[offset+j]) for j in range(2)]})})
            batches.append({"response":json.dumps({"decision":"PASS","issues":[]})})
        calls=[]
        def fake(_model,payload,*_args):
            calls.append(payload["messages"][0]["content"])
            return batches.pop(0)
        result=planner.build_plan(story,fake,"account","token")
        self.assertEqual([x["scene"] for x in result],list(range(1,7)))
        self.assertEqual(len(calls),6)
        self.assertIn("BATCH SCRIPT",calls[0])
        self.assertIn("PREVIOUS APPROVED SHOTS",calls[2])
        self.assertIn('"scene": 2',calls[2])
        self.assertEqual(len(batches),0)


    def test_later_chunk_prompt_forbids_previous_camera_triples(self):
        story={"title":"Ocean","scenes":[
            {"narration":"Ocean waves rise above the shoreline during the tide."},
            {"narration":"Cloud droplets form above the coastal ocean water."},
            {"narration":"Mist rises from the deep ocean into the air."},
            {"narration":"Rain falls from dark clouds onto the sea surface."},
            {"narration":"Sea foam gathers along the moving ocean shoreline."}]}
        first={"shots":[
            shot(1,"wide","side","establish","Coastal waves",
                 "Ocean waves roll up against the curved coastline."),
            shot(2,"close","frontal","detail","Cloud droplets",
                 "Small droplets cluster inside thick clouds over the ocean.")]}
        second={"shots":[
            shot(1,"medium","high","process","Rising mist",
                 "Thin mist rises from warm ocean water toward the sky."),
            shot(2,"extreme_wide","overhead","contrast","Rain at sea",
                 "Rain descends from dark clouds onto the open sea.")]}
        last={"shots":[shot(1,"extreme_close","low","consequence","Sea foam",
                "Small patches of sea foam gather along a breaking wave.")]}
        answers=[{"response":json.dumps(x)} for x in (
            first,{"decision":"PASS","issues":[]},
            second,{"decision":"PASS","issues":[]},
            last,{"decision":"PASS","issues":[]})]
        prompts=[]
        def fake(_model,payload,*_args):
            prompts.append(payload["messages"][0]["content"])
            return answers.pop(0)
        result=planner.build_plan(story,fake,"account","token")
        self.assertEqual(len(result),5)
        self.assertIn("wide / side / establish",prompts[2])
        self.assertIn("close / frontal / detail",prompts[2])
        self.assertIn("medium / high / process",prompts[4])
        self.assertIn("FORBIDDEN",prompts[2])


    def test_short_action_in_second_chunk_repaired_without_rewriting_other_shots(self):
        story={"title":"Ocean processes","scenes":[
            {"narration":"Ocean waves roll upward along the rugged shoreline."},
            {"narration":"Rain drops fall into coastal sea water from clouds."},
            {"narration":"Ocean mist rises from warm water into the atmosphere."},
            {"narration":"Wind pushes wave crests across the open ocean."},
            {"narration":"Sea foam gathers near the shoreline at dawn."}]}
        batch1={"shots":[
            shot(1,"wide","side","establish","Coastal waves",
                 "Ocean waves roll up against the nearby shoreline."),
            shot(2,"close","frontal","detail","Rain droplets",
                 "Rain droplets fall from clouds onto coastal water.")]}
        batch2={"shots":[
            shot(1,"medium","high","process","Ocean mist","mist"),
            shot(2,"extreme_wide","overhead","contrast","Wind-driven waves",
                 "Wind pushes small wave crests across an open sea.")]}
        patch={"scene":1,"scale":"medium","angle":"high","role":"process",
               "subject":"Ocean mist rising upward",
               "visible_action":"A thin layer of ocean mist rises from warm coastal water."}
        batch3={"shots":[shot(1,"extreme_close","low","consequence","Sea foam",
                              "Foam gathers along the edge of a shallow ocean wave.")]}
        answers=[batch1,{"decision":"PASS","issues":[]},
                 batch2,patch,{"decision":"PASS","issues":[]},
                 batch3,{"decision":"PASS","issues":[]}]
        calls=[]
        def fake(_model,payload,*_args):
            calls.append(payload["messages"][0]["content"])
            return {"response":json.dumps(answers.pop(0))}
        result=planner.build_plan(story,fake,"account","token")
        self.assertEqual(len(result),5)
        self.assertEqual(result[2]["visible_action"],patch["visible_action"])
        self.assertEqual(result[3]["visible_action"],batch2["shots"][1]["visible_action"])
        self.assertIn("Fix ONLY the subject",calls[3])

    def test_full_shot_repair_cannot_change_frozen_camera_metadata(self):
        story={"scenes":[
            {"narration":"Clouds float across the ocean over the summer season."}
            for _ in range(5)]}
        batch={"shots":[
            shot(1,"wide","side","establish","Ocean clouds","clouds"),
            shot(2,"close","frontal","detail","Ocean cloud edge",
                 "A long white cloud moves over the sea surface.")]}
        patch={"scene":1,"scale":"close","angle":"side","role":"establish",
               "subject":"Clouds over water",
               "visible_action":"Clouds drift above the distant ocean water below."}
        replies=[batch,patch]
        def fake(*args):
            return {"response":json.dumps(replies.pop(0))}
        with self.assertRaisesRegex(ValueError,"Single-shot batch repair returned invalid fields"):
            planner.build_plan(story,fake,"account","token")


    def test_timed_out_critic_retries_same_text_request_and_still_validates(self):
        calls=[]
        def fake(_model,payload,*_args):
            calls.append(payload["messages"][0]["content"])
            if len(calls)==1:
                return {"response":json.dumps(VALID)}
            if len(calls)==2:
                raise TimeoutError("read timed out")
            return {"response":json.dumps({"decision":"PASS","issues":[]})}
        shots=planner.build_plan(STORY,fake,"account","token")
        self.assertEqual(len(shots),3)
        self.assertEqual(len(calls),3)
        self.assertEqual(calls[1],calls[2])

    def test_repeated_text_timeout_fails_closed_before_images(self):
        calls=[]
        def fake(_model,payload,*_args):
            calls.append(payload)
            raise TimeoutError("read timed out")
        with self.assertRaises(TimeoutError):
            planner.build_plan(STORY,fake,"account","token")
        self.assertEqual(len(calls),2)

    def test_non_timeout_url_error_is_not_retried(self):
        import urllib.error
        calls=[]
        def fake(*_args):
            calls.append(1)
            raise urllib.error.URLError("DNS failure")
        with self.assertRaises(urllib.error.URLError):
            planner.build_plan(STORY,fake,"account","token")
        self.assertEqual(len(calls),1)

    def test_checkpoint_resumes_after_timeout_without_repeating_verified_shots(self):
        story={"title":"Ocean scenes","scenes":[
            {"narration":"Tidal waves form along the deep ocean shore."},
            {"narration":"Rain droplets fall into the deep ocean surface."},
            {"narration":"Cloud vapors condense above the wide blue sea."},
            {"narration":"Sea foam spreads across a moving wavefront."},
            {"narration":"The moon illuminates a long coastal shoreline."}]}
        first={"shots":[
            shot(1,"wide","side","establish","Ocean waves",
                 "Tidal waves form along the deep ocean shore."),
            shot(2,"close","frontal","detail","Ocean rainfall",
                 "Rain droplets fall into the deep ocean surface.")]}
        second={"shots":[
            shot(1,"medium","high","process","Condensing clouds",
                 "Cloud vapors condense above the wide blue sea."),
            shot(2,"extreme_wide","overhead","contrast","Moving foam",
                 "Sea foam spreads across a moving wavefront.")]}
        last={"shots":[
            shot(1,"extreme_close","low","consequence","Moonlit coast",
                 "The moon illuminates a long coastal shoreline.")]}
        with tempfile.TemporaryDirectory() as d:
            cp=Path(d)/"resume.json"
            answers=[first,{"decision":"PASS","issues":[]}]
            def interrupted(_model,_payload,*_args):
                if not answers:
                    raise TimeoutError("transient upstream timeout")
                answer=answers.pop(0)
                return {"response":json.dumps(answer)}
            with self.assertRaises(TimeoutError):
                planner.build_plan(story,interrupted,"account","secret",
                                   checkpoint_path=cp)
            self.assertTrue(cp.is_file())
            cache=json.loads(cp.read_text())
            self.assertEqual(len(cache["accepted_shots"]),2)
            self.assertFalse(cache["ready_to_publish"])
            remaining=[second,{"decision":"PASS","issues":[]},
                       last,{"decision":"PASS","issues":[]}]
            calls=[]
            def resumed(_model,payload,*_args):
                calls.append(payload["messages"][0]["content"])
                return {"response":json.dumps(remaining.pop(0))}
            shots=planner.build_plan(story,resumed,"account","secret",
                                     checkpoint_path=cp)
            self.assertEqual([x["scene"] for x in shots],list(range(1,6)))
            self.assertEqual(len(calls),4)
            self.assertIn("Cloud vapors condense",calls[0])
            self.assertNotIn("BATCH SCRIPT (local scene numbers):\n1. Tidal waves",calls[0])
            self.assertEqual(len(json.loads(cp.read_text())["accepted_shots"]),5)
            def no_requests(*args):
                raise AssertionError("Already approved plan should not rerun AI")
            self.assertEqual(planner.build_plan(story,no_requests,"account","secret",
                                                checkpoint_path=cp),shots)

    def test_checkpoint_rejects_modified_story_and_forged_shots(self):
        story={"title":"Ocean","scenes":[
            {"narration":"Long ocean waves roll toward a sandy shoreline."},
            {"narration":"Rain falls from clouds over a distant ocean."},
            {"narration":"Sea mist rises from the surface of warm water."},
            {"narration":"Clouds move across the open coastal night sky."},
            {"narration":"The moon shines above a long coastal beach."}]}
        accepted=[shot(1,"wide","side","establish","Ocean waves",
                       "Long ocean waves roll toward a sandy shoreline."),
                  shot(2,"close","frontal","detail","Ocean rainfall",
                       "Rain falls from clouds over a distant ocean.")]
        with tempfile.TemporaryDirectory() as d:
            cp=Path(d)/"saved.json"
            planner._write_checkpoint(cp,story,accepted,2,"secret")
            self.assertEqual(planner._read_checkpoint(cp,story,"secret")[0],accepted)
            altered=json.loads(json.dumps(story))
            altered["scenes"][0]["narration"]="A different ocean story begins here."
            with self.assertRaisesRegex(ValueError,"Untrusted"):
                planner._read_checkpoint(cp,altered,"secret")
            with self.assertRaisesRegex(ValueError,"Untrusted"):
                planner._read_checkpoint(cp,story,"wrong-token")
            data=json.loads(cp.read_text())
            data["accepted_shots"][0]["visible_action"]="A new galaxy appears."
            cp.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"Untrusted"):
                planner._read_checkpoint(cp,story,"secret")

    def test_checkpoint_rejects_invalid_json_without_calling_ai(self):
        story={"title":"Ocean","scenes":[
            {"narration":"Waves rise along the ocean coast in morning light."}
            for _ in range(5)]}
        with tempfile.TemporaryDirectory() as d:
            cp=Path(d)/"saved.json"
            cp.write_text('{"accepted_shots": [')
            calls=[]
            def fake(*args):
                calls.append(1)
            with self.assertRaisesRegex(ValueError,"Untrusted"):
                planner.build_plan(story,fake,"account","secret",checkpoint_path=cp)
            self.assertEqual(calls,[])

    def test_malformed_second_batch_falls_back_to_one_scene_with_prefix(self):
        story={"title":"Ocean","scenes":[
            {"narration":"Tidal waves form along the distant ocean shore."},
            {"narration":"Rain droplets fall into the deep ocean surface."},
            {"narration":"Cloud vapors condense above the blue sea."},
            {"narration":"Sea foam spreads across a moving wavefront."},
            {"narration":"The moon illuminates a coastal shoreline."}]}
        first={"shots":[
            shot(1,"wide","side","establish","Ocean waves",
                 "Tidal waves form along the distant ocean shore."),
            shot(2,"close","frontal","detail","Ocean rainfall",
                 "Rain droplets fall into the deep ocean surface.")]}
        single=[
            shot(1,"medium","high","process","Cloud vapors",
                 "Cloud vapors condense above the open blue sea."),
            shot(1,"extreme_wide","overhead","contrast","Sea foam",
                 "Sea foam spreads across a moving wavefront."),
            shot(1,"extreme_close","low","consequence","Moonlit coast",
                 "The moon illuminates a distant coastal shoreline.")]
        replies=[first,{"decision":"PASS","issues":[]},
                 "{bad","{bad"]
        for item in single:
            replies.extend([{"shots":[item]},{"decision":"PASS","issues":[]}])
        calls=[]
        def fake(_model,payload,*_args):
            calls.append(payload["messages"][0]["content"])
            item=replies.pop(0)
            return {"response":item if isinstance(item,str) else json.dumps(item)}
        shots=planner.build_plan(story,fake,"account","token")
        self.assertEqual(len(shots),5)
        self.assertEqual([x["scene"] for x in shots],[1,2,3,4,5])
        self.assertEqual(len(calls),10)
        self.assertIn("EXACTLY 1 objects",calls[4])
        self.assertIn("wide / side / establish",calls[4])

    def test_cross_batch_duplicate_repairs_only_repeated_scene(self):
        story={"title":"Ocean processes","scenes":[
            {"narration":"Ocean waves move across a coastal sea surface."},
            {"narration":"Rain droplets fall from thick clouds above the ocean."},
            {"narration":"Ocean waves and moving water strike the coastline."},
            {"narration":"The moon lights the water surface at night."},
            {"narration":"Wind pushes high clouds above an open ocean."}]}
        original_action="Ocean waves move across a coastal sea surface."
        first={"shots":[
            shot(1,"wide","side","establish","Ocean waves",original_action),
            shot(2,"close","frontal","detail","Rainfall",
                 "Rain droplets fall from thick clouds above the ocean.")]}
        second={"shots":[
            shot(1,"medium","high","process","Ocean coastline",original_action),
            shot(2,"extreme_wide","overhead","contrast","Moonlit sea",
                 "The distant moon lights the sea surface at night.")]}
        patch={"subject":"Coastline breaking waves",
               "visible_action":"A curling wave breaks against the coastline with visible white foam."}
        final={"shots":[shot(1,"extreme_close","low","consequence",
                             "High clouds and wind",
                             "Wind pushes a high cloud bank across the ocean sky.")]}
        answers=[first,{"decision":"PASS","issues":[]},second,patch,
                 {"decision":"PASS","issues":[]},final,
                 {"decision":"PASS","issues":[]}]
        prompts=[]
        def fake(_model,payload,*_args):
            prompts.append(payload["messages"][0]["content"])
            return {"response":json.dumps(answers.pop(0))}
        output=planner.build_plan(story,fake,"account","token")
        self.assertEqual([x["scene"] for x in output],[1,2,3,4,5])
        self.assertEqual(output[0]["visible_action"],original_action)
        self.assertEqual(output[2]["visible_action"],patch["visible_action"])
        self.assertEqual(output[3]["visible_action"],second["shots"][1]["visible_action"])
        self.assertIn("DUPLICATED EARLIER SHOT",prompts[3])
        self.assertEqual(len(prompts),7)

    def test_cross_batch_duplicate_repair_still_rejects_same_action(self):
        story={"title":"Ocean","scenes":[
            {"narration":"Ocean waves move across a coastal sea surface."},
            {"narration":"Rain droplets fall from thick clouds above the ocean."},
            {"narration":"Ocean waves and moving water strike the coastline."},
            {"narration":"The moon lights the water surface at night."},
            {"narration":"Wind pushes high clouds above the sea."}]}
        repeated="Ocean waves move across a coastal sea surface."
        first={"shots":[
            shot(1,"wide","side","establish","Ocean waves",repeated),
            shot(2,"close","frontal","detail","Rain droplets",
                 "Raindrops fall from dark clouds into the open ocean.")]}
        second={"shots":[
            shot(1,"medium","high","process","Ocean waves",repeated),
            shot(2,"extreme_wide","overhead","contrast","Moonlight",
                 "Moonlight illuminates the wide sea surface at night.")]}
        answers=[first,{"decision":"PASS","issues":[]},second,
                 {"subject":"Ocean waves","visible_action":repeated}]
        calls=[]
        def fake(_model,payload,*_args):
            calls.append(1)
            return {"response":json.dumps(answers.pop(0))}
        with self.assertRaisesRegex(ValueError,"failed twice"):
            planner.build_plan(story,fake,"account","token")
        self.assertEqual(len(calls),4)

    def test_bad_long_story_batch_retries_only_that_batch_then_blocks(self):
        lines=[
            "Tidal waves form along the distant ocean shore.",
            "Rain droplets fall into the deep ocean surface.",
            "Cloud vapors condense above the blue sea.",
            "Sea foam spreads across a moving wavefront.",
            "The moon illuminates a coastal shoreline.",
            "Moving air pushes a gentle sea current."
        ]
        story={"title":"Tides","scenes":[{"narration":x} for x in lines]}
        first={"shots":[
            shot(1,"wide","side","establish","Waves at sea",
                 "Tidal waves move above the shoreline at dawn."),
            shot(2,"close","frontal","detail","Raindrops at sea",
                 "Rain drops fall into the ocean surface below.")]}
        replies=[{"response":json.dumps(first)},
                 {"response":'{"decision":"PASS","issues":[]}'},
                 {"response":"{broken"},{"response":"{broken"},
                 {"response":"{broken"},{"response":"{broken"}]
        calls=[]
        def fake(_model,payload,*_args):
            calls.append(payload["messages"][0]["content"])
            return replies.pop(0)
        with self.assertRaisesRegex(ValueError,"Shot batch 3 failed twice"):
            planner.build_plan(story,fake,"account","token")
        self.assertEqual(len(calls),6)
        self.assertIn("PREVIOUS BATCH FAILED",calls[-1])

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
