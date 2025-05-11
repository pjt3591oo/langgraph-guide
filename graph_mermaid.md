---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	search(search)
	generate_answer(generate_answer)
	request_clarification(request_clarification)
	__end__([<p>__end__</p>]):::last
	__start__ --> search;
	search -. &nbsp;generate&nbsp; .-> generate_answer;
	search -. &nbsp;clarify&nbsp; .-> request_clarification;
	generate_answer --> __end__;
	request_clarification --> __end__;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc
