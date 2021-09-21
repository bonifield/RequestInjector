from setuptools import setup

setup(
	py_modules=["requestinjector"],
	entry_points={
		"console_scripts":[
			"requestinjector = requestinjector:tool_entrypoint",
			"ri = requestinjector:tool_entrypoint"
		]
	}
)