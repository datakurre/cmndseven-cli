// rollup.config.js
import commonjs from "@rollup/plugin-commonjs";
import json from "@rollup/plugin-json";
import replace from "@rollup/plugin-replace";
import resolve from "@rollup/plugin-node-resolve";

export default [{
  input: "bpmn-viewer.js",
  output: {
    file: "bpmn-viewer.production.min.js",
    format: "iife"
  },
  plugins: [
    replace({
      "process.env.NODE_ENV": JSON.stringify("production"),
      preventAssignment: true
    }),
    resolve(),
    json(),
    commonjs()
  ]
}];
