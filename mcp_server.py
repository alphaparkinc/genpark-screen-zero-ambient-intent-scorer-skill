# -*- coding: utf-8 -*-
"""
Glance Screen Zero Ambient Intent Scorer MCP Server
Exposes screen zero intent scoring tools via standard JSON-RPC 2.0 over STDIO.
"""

import sys
import json
from client import GlanceScreenZeroAmbientIntentScorer

def handle_request(req):
    method = req.get("method")
    req_id = req.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "glance-screen-zero-ambient-intent-scorer", "version": "1.0.0"}
            }
        }
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "score_ambient_intent",
                        "description": "Evaluates lock-screen dwell attention, swipe physics, and circadian context to predict zero-click purchase intent.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "dwell_time_sec": {"type": "number", "description": "Gaze/dwell duration in seconds"},
                                "swipe_velocity_px_s": {"type": "number", "description": "Touch swipe velocity in px/s"},
                                "swipe_angle_deg": {"type": "number", "description": "Angle of swipe in degrees (0 = horizontal)"},
                                "wake_hour_of_day": {"type": "integer", "description": "Hour of device wake event (0-23)"},
                                "wake_frequency_last_hour": {"type": "integer", "description": "Number of wakes in preceding 60 minutes"}
                            },
                            "required": ["dwell_time_sec"]
                        }
                    }
                ]
            }
        }
    elif method == "tools/call":
        params = req.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})

        if tool_name == "score_ambient_intent":
            scorer = GlanceScreenZeroAmbientIntentScorer()
            res = scorer.score_ambient_intent(
                dwell_time_sec=args.get("dwell_time_sec", 1.8),
                swipe_velocity_px_s=args.get("swipe_velocity_px_s", 0.0),
                swipe_angle_deg=args.get("swipe_angle_deg", 0.0),
                wake_hour_of_day=args.get("wake_hour_of_day", 12),
                wake_frequency_last_hour=args.get("wake_frequency_last_hour", 3),
                historical_category_affinities=args.get("historical_category_affinities")
            )
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}
            }
        else:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Tool '{tool_name}' not found"}}
    else:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32600, "message": f"Method '{method}' not supported"}}

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("MCP Server Discovery Test OK")
        scorer = GlanceScreenZeroAmbientIntentScorer()
        test_res = scorer.score_ambient_intent(2.4, 150.0, 15.0, 21, 5)
        print(f"Test Score: {test_res['composite_intent_score']}")
        return

    for line in sys.stdin:
        if not line.strip(): continue
        try:
            req = json.loads(line)
            resp = handle_request(req)
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(e)}}
            sys.stdout.write(json.dumps(err) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
