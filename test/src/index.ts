import { Ollama } from "@langchain/ollama";

const model = new Ollama({
  model: "llama3",
});

const response = await model.invoke("Explain TypeScript in simple words.");

console.log(response);