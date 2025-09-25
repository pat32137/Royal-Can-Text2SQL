
orchestrate env activate t2s-env
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

orchestrate tools import -k openapi -f ${SCRIPT_DIR}/tool/openapi_text2sql_stgb.json
orchestrate agents import -f ${SCRIPT_DIR}/agent/text2sql_agent.yaml
