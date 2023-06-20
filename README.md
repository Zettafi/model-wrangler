Model Wrangler
==============

Model wrangler is a tool to quickly execute models or host them via an OpenAPI/Swagger
compliant HTTP API with SwaggerUI included.

Supported Models
----------------

Hugging Face text to text transformer and text to image transformer models are
currently supported.

Running the Wrangler
--------------------

Wrangler is a command line interface (CLI) application with contextual help. 

```bash
wrangler help
```

### Run

The `run` subcommand will provide supplied text to a defined model

### Serve

The `serve` subcommand will start a webserver to supply input to a defined model.
Information about the input and output as well as an interactive experience is provided
at `/docs`.

### Examples

Here are some quick examples that don;t require GPU to validate a working system.
The models used are utilized for integration testing, so they are fairly quick.

#### Run Text Generation

Running the following example command will print out the input appended with seemingly
random text.

##### Command
```bash
 wrangler run text-transform hf-internal-testing/tiny-random-gpt2 How now brown
```

##### Example Output
```
How now brownathathcccccccccccccccccccccc
```

#### Serve Text Generation

Running the following example will host a model in an API that will return the
input appended with seemingly random text.

##### Command
```bash
 wrangler serve text-transform hf-internal-testing/tiny-random-gpt2
```

##### Example Input
```json
{
  "input": "How now brown"
}
```

##### Example Output
```json
{
  "generated_text": "How now brownathathcccccccccccccccccccccc"
}
```

#### Run Image Generation

Running the following example will generate a small pixelated image in the file
`/tmp/brown-cow.png`.

##### Command
```bash
 wrangler run image-generate hf-internal-testing/unidiffuser-test-v1 /tmp/brown-cow.png Brown Cow
```
#### Serve Image Generation

Running the following example will host a model in an API that will return a seemingly
random pixelated image with is base64 encoded.

##### Command
```bash
 wrangler serve image-generate hf-internal-testing/unidiffuser-test-v1
```

##### Example Input
```json
{
  "input": "Brown Cow"
}
```

##### Example Output
```json
{
  "image": "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",
  "format": "PNG"
}
```
