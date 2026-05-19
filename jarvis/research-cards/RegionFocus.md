# Research Card: RegionFocus

source_project: RegionFocus
source_url: https://github.com/tiangeluo/RegionFocus
source_revision: `f69575db87a7402cf4b859f709eb51e1a3ff9b3e`

source_paths:
- `https://github.com/tiangeluo/RegionFocus/blob/f69575db87a7402cf4b859f709eb51e1a3ff9b3e/README.md`
- `https://github.com/tiangeluo/RegionFocus/blob/f69575db87a7402cf4b859f709eb51e1a3ff9b3e/eval_screenspot_pro_RegionFocus.py`
- `https://github.com/tiangeluo/RegionFocus/blob/f69575db87a7402cf4b859f709eb51e1a3ff9b3e/models/uitars_RegionFocus.py`

mechanism_summary:
- RegionFocus 通过 initial grounding、judge、crop region、zoom/upsample、projection back to original 来提升视觉定位。
- debug 模式保存 image-as-map stars、zoom-ins、projected predictions 和 judgment response。
- 视觉判断强调中间证据，而不只输出最终坐标。

jarvis_mapping:
- 映射为 Visual Evidence Loop 接口。
- OCR/图片结论必须保留截图、裁剪区域、二次查看和置信度，而不是直接写事实。

adopted_parts:
- 中间视觉证据。
- zoom-in / crop 后复核。
- 原图坐标回投。

rejected_parts:
- 不接入 RegionFocus 模型。
- 不实现 GUI grounding。
- 不把视觉/OCR claim 直接入库。

usable_rule:
- 对图片、截图、OCR claim，Evidence Pack 必须标注 `source_type=image`，并记录原图、裁剪/缩放证据和验证状态。

test_case:
- 输入：基于截图判断某 UI 文案。
- 期望：先输出视觉证据链和待确认 claim；证据不足时标 `verification_status=needs_review`。

failure_trigger_for_research:
- 视觉/OCR claim 缺中间证据或无法追溯原图时，回到 RegionFocus image-as-map / zoom-in debug 输出重新研究。
