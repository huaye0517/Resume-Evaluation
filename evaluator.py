# -*- coding: utf-8 -*-
"""简历评估核心模块。

负责构建发给 DeepSeek 的提示词，调用模型，并把返回的 JSON
规整为统一结构，供网页展示和 Excel 导出使用。
"""

from deepseek_client import chat_json, DeepSeekError


# 系统提示词：设定资深招聘官角色与评估标准
SYSTEM_PROMPT = """你是一名资深招聘官（HR）和用人专家，擅长根据岗位 JD 快速筛选简历，判断候选人是否值得发出面试邀约。

你熟悉以下类型岗位的用人标准：抖音内容营销主管/经理、渠道分销专员、抖音内容素材主管、招聘主管、电商总账会计等。

评估原则：
1. 先看硬性条件是否满足（如岗位方向、相关行业经验年限、必备技能/证书、学历要求等）。
2. 再看软性匹配（项目经历相关度、成长性、稳定性、与岗位画像的契合度）。
3. 客观、务实，不夸大也不苛刻；理由必须基于简历事实，不要编造简历中没有的信息。
4. 如果简历信息不足以判断某项，应在风险点中指出，而不是臆测。

你必须只输出一个 JSON 对象，不要输出任何额外说明文字。"""


# 用户提示词模板：要求模型严格按字段输出 JSON
USER_PROMPT_TEMPLATE = """请根据下面的【岗位 JD】评估【候选人简历】是否适合发出面试邀约。

【岗位 JD】
{jd_text}

【候选人简历】
{resume_text}

请严格按以下 JSON 结构输出（字段名保持英文，内容用中文）：
{{
  "candidate_name": "从简历中提取的候选人姓名，找不到则填 '未知'",
  "verdict": "只能是以下三选一：适合 / 待定 / 不适合",
  "score": 0到100的整数，表示与岗位的总体匹配度,
  "dimension_scores": {{
    "岗位方向匹配": 0到100的整数,
    "相关经验": 0到100的整数,
    "专业技能": 0到100的整数,
    "稳定性与成长性": 0到100的整数
  }},
  "highlights": ["亮点1", "亮点2"],
  "risks": ["风险点或不匹配点1", "风险点2"],
  "interview_questions": ["建议在面试中考察的问题1", "问题2", "问题3"],
  "summary": "一句话总结评估结论及主要理由"
}}"""


# 统一的结果字段，确保展示与导出时结构稳定
_DEFAULT_DIMENSIONS = {
    "岗位方向匹配": 0,
    "相关经验": 0,
    "专业技能": 0,
    "稳定性与成长性": 0,
}


def _normalize_result(raw):
    """把模型返回的原始 JSON 规整为统一结构，缺失字段补默认值。"""
    def _as_int(value, default=0):
        try:
            return int(round(float(value)))
        except (TypeError, ValueError):
            return default

    def _as_list(value):
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if value:
            return [str(value).strip()]
        return []

    verdict = str(raw.get("verdict", "待定")).strip()
    if verdict not in ("适合", "待定", "不适合"):
        verdict = "待定"

    dimensions = dict(_DEFAULT_DIMENSIONS)
    raw_dimensions = raw.get("dimension_scores") or {}
    if isinstance(raw_dimensions, dict):
        for key, val in raw_dimensions.items():
            dimensions[str(key)] = _as_int(val)

    return {
        "candidate_name": str(raw.get("candidate_name", "未知")).strip() or "未知",
        "verdict": verdict,
        "score": max(0, min(100, _as_int(raw.get("score")))),
        "dimension_scores": dimensions,
        "highlights": _as_list(raw.get("highlights")),
        "risks": _as_list(raw.get("risks")),
        "interview_questions": _as_list(raw.get("interview_questions")),
        "summary": str(raw.get("summary", "")).strip(),
        "error": None,
    }


def evaluate_resume(jd_text, resume_text, filename):
    """评估单份简历，返回统一结构的结果字典。

    调用或解析失败时，返回带 error 字段的占位结果，不抛出异常。
    """
    user_prompt = USER_PROMPT_TEMPLATE.format(jd_text=jd_text, resume_text=resume_text)

    try:
        raw = chat_json(SYSTEM_PROMPT, user_prompt)
        result = _normalize_result(raw)
    except DeepSeekError as exc:
        result = _build_error_result(f"模型评估失败：{exc}")
    except Exception as exc:
        result = _build_error_result(f"评估异常：{exc}")

    result["filename"] = filename
    return result


def _build_error_result(error_message):
    """构造一个标记错误的结果，保证字段结构与正常结果一致。"""
    return {
        "candidate_name": "未知",
        "verdict": "无法评估",
        "score": 0,
        "dimension_scores": dict(_DEFAULT_DIMENSIONS),
        "highlights": [],
        "risks": [],
        "interview_questions": [],
        "summary": error_message,
        "error": error_message,
    }


def build_parse_error_result(filename, error_message):
    """简历解析失败时，生成对应的占位结果。"""
    result = _build_error_result(error_message)
    result["filename"] = filename
    return result
