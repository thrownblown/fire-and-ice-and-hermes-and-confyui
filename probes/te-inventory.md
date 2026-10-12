# Text encoder inventory
Root: `E:/comfymodels/models`

| file | GB | arch | lm_head | vision | layers | dtype/quant | verdict |
|---|---|---|---|---|---|---|---|
| text_encoders\Huihui-Qwen3-VL-4B-Instruct-abliterated-fp8_scaled.safetensors | 5.2 | decoder-LLM (arch ?) | False | True | 36 | fp8_scaled | vision tower but no lm_head (can't talk) |
| text_encoders\Josiefied-Qwen3-4B-abliterated-v1.i1-Q6_K.gguf | 3.3 | qwen3 | ? | ? | 0 | gguf | GGUF: try LM Studio directly (vision needs an mmproj) |
| text_encoders\Qwen3-4B-Q8_0.gguf | 4.3 | qwen3 | ? | ? | 0 | gguf | GGUF: try LM Studio directly (vision needs an mmproj) |
| text_encoders\Qwen3-4B-abliterated-v2.safetensors | 8.0 | decoder-LLM (arch ?) | False | False | 36 | BF16 | no (truncated encoder) |
| text_encoders\Qwen3-4B-abliterated.safetensors | 8.0 | decoder-LLM (arch ?) | False | False | 36 | BF16 | no (truncated encoder) |
| text_encoders\Qwen3VL-8B-Uncensored-HauhauCS-Aggressive-Q8_0.gguf | 8.7 | qwen3vl | ? | ? | 0 | gguf | GGUF: try LM Studio directly (vision needs an mmproj) |
| text_encoders\clip_l.safetensors | 0.2 | clip | False | False | 12 | F16 | no (encoder-only, can't generate text) |
| text_encoders\gemma-3-12b-abliterated-text-encoder.safetensors | 23.5 | decoder-LLM (arch ?) | False | False | 48 | BF16,U8 | no (truncated encoder) |
| text_encoders\gemma-3-12b-it-abliterated.q6_k.gguf | 9.7 | gemma3 | ? | ? | 0 | gguf | GGUF: try LM Studio directly (vision needs an mmproj) |
| text_encoders\gemma-3-12b-it-abliterated.safetensors | 24.4 | decoder-LLM (arch ?) | False | True | 48 | BF16 | vision tower but no lm_head (can't talk) |
| text_encoders\huihui-qwen3-8b-abliterated-v2-q8_0.gguf | 8.7 | qwen3 | ? | ? | 0 | gguf | GGUF: try LM Studio directly (vision needs an mmproj) |
| text_encoders\nsfw_wan_umt5-xxl_bf16.safetensors | 11.4 | t5/umt5 | False | False | 0 | BF16 | no (encoder-only, can't generate text) |
| text_encoders\nsfw_wan_umt5-xxl_fp8_scaled.safetensors | 6.7 | t5/umt5 | False | False | 0 | F16,F8_E4M3,U8 | no (encoder-only, can't generate text) |
| text_encoders\qwen-josie.safetensors | 8.0 | decoder-LLM (arch ?) | False | False | 36 | BF16 | no (truncated encoder) |
| text_encoders\qwen3-vl-4b-heretic_fp8_e4m3fn.safetensors | 4.4 | decoder-LLM (arch ?) | False | True | 36 | fp8_scaled | vision tower but no lm_head (can't talk) |
| text_encoders\qwen3VL4BAbliteratedComfyui_v10.safetensors | 4.8 | decoder-LLM (arch ?) | False | True | 36 | BF16,F8_E4M3 | vision tower but no lm_head (can't talk) |
| text_encoders\qwen3VL4BAbliteratedComfyui_v10_bf16.safetensors | 8.9 | decoder-LLM (arch ?) | False | True | 36 | BF16 | vision tower but no lm_head (can't talk) |
| text_encoders\qwen3vl-4b-abliterated_fp8_e4m3fn.safetensors | 4.8 | decoder-LLM (arch ?) | False | True | 36 | BF16,F8_E4M3 | vision tower but no lm_head (can't talk) |
| text_encoders\qwen3vl_32b_h3_instruct_generation_tail_50_63_int8_convrot.safetensors | 7.6 | decoder-LLM (arch ?) | True | False | 64 | fp8_scaled | text LLM only (no vision) |
| text_encoders\qwen3vl_32b_h3_instruct_generation_tail_50_63_nvfp4_awq.safetensors | 5.4 | decoder-LLM (arch ?) | True | False | 64 | fp8_scaled | text LLM only (no vision) |
| text_encoders\qwen_2.5_vl_7b_fp8_scaled.safetensors | 9.4 | decoder-LLM (arch ?) | True | True | 28 | fp8_scaled | CANDIDATE VLM (needs conversion to HF/GGUF) |
| text_encoders\qwen_3_8b_fp4mixed.safetensors | 6.8 | decoder-LLM (arch ?) | False | False | 36 | fp8_scaled | no (truncated encoder) |
| text_encoders\t5xxl_fp8_e4m3fn.safetensors | 4.9 | t5/umt5 | False | False | 0 | F8_E4M3 | no (encoder-only, can't generate text) |
| text_encoders\t5xxl_fp8_e4m3fn_scaled.safetensors | 5.2 | t5/umt5 | False | False | 0 | fp8_scaled | no (encoder-only, can't generate text) |
| text_encoders\umt5-xxl-enc-bf16.safetensors | 11.4 | ? | False | False | 0 | BF16 | no (truncated encoder) |
| text_encoders\umt5-xxl-enc-fp8_e4m3fn.safetensors | 6.7 | ? | False | False | 0 | BF16,F8_E4M3 | no (truncated encoder) |
| text_encoders\umt5-xxl-encoder-Q8_0.gguf | 6.0 | t5encoder | ? | ? | 0 | gguf | GGUF: try LM Studio directly (vision needs an mmproj) |
| text_encoders\umt5_xxl_fp8_e4m3fn_scaled.safetensors | 6.7 | t5/umt5 | False | False | 0 | fp8_scaled | no (encoder-only, can't generate text) |
| clip\apple_DFN5B-CLIP-ViT-H-14-384_fp16.safetensors | 2.0 | ? | False | True | 0 | F16 | vision tower but no lm_head (can't talk) |
| LLM\Florence-2-base-PromptGen-v2.0\model.safetensors | 1.1 | decoder-LLM (arch ?) | True | True | 6 | F32 | CANDIDATE VLM (needs conversion to HF/GGUF) |
| llm\Florence-2-base-PromptGen-v2.0\model.safetensors | 1.1 | decoder-LLM (arch ?) | True | True | 6 | F32 | CANDIDATE VLM (needs conversion to HF/GGUF) |
