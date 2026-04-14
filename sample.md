---
title: "Azure OpenAI Chat"
category: "Chat"
source: "Azure OpenAI Chat __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# Azure OpenAI Chat

## Azure OpenAI Chat
Prerequisites
Azure API Key & Endpoint
OpenAI Key
Microsoft Entra ID
Deployment Name
Add Repositories and BOM
Auto-configuration
Chat Properties
Token Limit Parameters: Model-Specific Usage
Runtime Options
Function Calling
Multimodal
Sample Controller
Manual Configuration
Azure’s OpenAI offering, powered by ChatGPT, extends beyond traditional OpenAI capabilities, delivering AI-driven text generation with en‐
hanced functionality. Azure offers additional AI safety and responsible AI features, as highlighted in their recent update here.
Azure offers Java developers the opportunity to leverage AI’s full potential by integrating it with an array of Azure services, which includes
AI-related resources such as Vector Stores on Azure.
```yaml
1/17
```

|  |
| --- |
| Spring AI / Reference / Models / Chat Models / Azure OpenAI |

Prerequisites
The Azure OpenAI client offers three options to connect: using an Azure API key or using an OpenAI API Key, or using Microsoft Entra ID.
Azure API Key & Endpoint
To access models using an API key, obtain your Azure OpenAI and from the Azure OpenAI Service section on the
endpoint api-key
Azure Portal.
Spring AI defines two configuration properties:
1. spring.ai.azure.openai.api-key: Set this to the value of the obtained from Azure.
API Key
2. spring.ai.azure.openai.endpoint: Set this to the endpoint URL obtained when provisioning your model in Azure.
You can set these configuration properties in your or file:
application.properties application.yml
```properties
spring.ai.azure.openai.api-key=<your-azure-api-key>
spring.ai.azure.openai.endpoint=<your-azure-endpoint-url>
```
For enhanced security when handling sensitive information like API keys, you can use Spring Expression Language (SpEL) to reference
custom environment variables:
# In application.yml
spring:
ai:
azure:
openai:
```yaml
api-key: ${AZURE_OPENAI_API_KEY}
endpoint: ${AZURE_OPENAI_ENDPOINT}
2/17
```

|  | YAML # In application.yml spring: ai: azure: openai: api-key: ${AZURE_OPENAI_API_KEY} endpoint: ${AZURE_OPENAI_ENDPOINT} |
| --- | --- |
|  |  |
|  |  |

## In your environment or .env file
export AZURE_OPENAI_API_KEY=<your-azure-openai-api-key>
export AZURE_OPENAI_ENDPOINT=<your-azure-openai-endpoint-url>
OpenAI Key
To authenticate with the OpenAI service (not Azure), provide an OpenAI API key. This will automatically set the endpoint to
api.openai.com/v1.
When using this approach, set the property to the name of the OpenAI
spring.ai.azure.openai.chat.options.deployment-name
model you wish to use.
In your application configuration:
```properties
spring.ai.azure.openai.openai-api-key=<your-azure-openai-key>
spring.ai.azure.openai.chat.options.deployment-name=<openai-model-name>
```
Using environment variables with SpEL:
## In application.yml
spring:
ai:
azure:
openai:
```yaml
openai-api-key: ${AZURE_OPENAI_API_KEY}
```
chat:
options:
```yaml
deployment-name: ${AZURE_OPENAI_MODEL_NAME}
```
## In your environment or .env file
export AZURE_OPENAI_API_KEY=<your-openai-key>
```yaml
3/17
```
export AZURE_OPENAI_MODEL_NAME=<openai-model-name>
Microsoft Entra ID
For keyless authentication using Microsoft Entra ID (formerly Azure Active Directory), set only the
spring.ai.azure.openai.endpoint
configuration property and not the api-key property mentioned above.
Finding only the endpoint property, your application will evaluate several different options for retrieving credentials and an
OpenAIClient
instance will be created using the token credentials.
It is no longer necessary to create a TokenCredential bean; it is configured for you automatically.
Deployment Name
To use Azure AI applications, you need to create an Azure AI Deployment through the Azure AI Portal. In Azure, each client must specify a
to connect to the Azure OpenAI service. It’s important to note that the is different from the model
Deployment Name Deployment Name
you choose to deploy. For example, a deployment named 'MyAiDeployment' could be configured to use either the GPT 3.5 Turbo model or
the GPT 4.0 model.
To get started, follow these steps to create a deployment with the default settings:
Deployment Name: `gpt-4o`
Model Name: `gpt-4o`
This Azure configuration aligns with the default configurations of the Spring Boot Azure AI Starter and its Autoconfiguration feature. If you
use a different Deployment Name, make sure to update the configuration property accordingly:
```properties
spring.ai.azure.openai.chat.options.deployment-name=<my deployment name>
4/17
```

|  | spring.ai.azure.openai.chat.options.deployment-name=<my deployment name> |
| --- | --- |
| spring | spring |
|  | spri |
|  |  |

The different deployment structures of Azure OpenAI and OpenAI leads to a property in the Azure OpenAI client library named
deploymentOrModelName. This is because in OpenAI there is no Name, only a Name.
Deployment Model
The property spring.ai.azure.openai.chat.options.model has been renamed to spring.ai.azure.openai.chat.options.deployment-
name.
If you decide to connect to instead of OpenAI, by setting the
OpenAI Azure spring.ai.azure.openai.openai-api-key=<Your OpenAI Key>
property, then the is treated as an OpenAI model name.
spring.ai.azure.openai.chat.options.deployment-name
Access the OpenAI Model
You can configure the client to use directly instead of the deployed models. For this you need to set the
OpenAI Azure OpenAI
```properties
spring.ai.azure.openai.openai-api-key=<Your OpenAI Key> instead of spring.ai.azure.openai.api-key=<Your Azure
```
Key>.
OpenAi
Add Repositories and BOM
Spring AI artifacts are published in Maven Central and Spring Snapshot repositories. Refer to the Artifact Repositories section to add these
repositories to your build system.
To help with dependency management, Spring AI provides a BOM (bill of materials) to ensure that a consistent version of Spring AI is used
throughout the entire project. Refer to the Dependency Management section to add the Spring AI BOM to your build system.
Auto-configuration
There has been a significant change in the Spring AI auto-configuration, starter modules' artifact names. Please refer to the upgrade notes for more
information.
```yaml
5/17
```

|  |  | There has been a significant change in the Spring AI auto-configuration, starter modules' artifact names. Please refer to the upgrade notes for more information. |
| --- | --- | --- |
| There inform |  | There inform |
|  |  | There inform |

Spring AI provides Spring Boot auto-configuration for the Azure OpenAI Chat Client. To enable it add the following dependency to your
project’s Maven or Gradle build files:
pom.xml build.gradle
Maven Gradle
```xml
<dependency>
<groupId>org.springframework.ai</groupId>
<artifactId>spring-ai-starter-model-azure-openai</artifactId>
</dependency>
```
Refer to the Dependency Management section to add the Spring AI BOM to your build file.
The Azure OpenAI Chat Client is created using the OpenAIClientBuilder provided by the Azure SDK. Spring AI allows to customize the
builder by providing AzureOpenAIClientBuilderCustomizer beans.
A customizer might be used for example to change the default response timeout:
```java
@Configuration
public class AzureOpenAiConfig {
@Bean
public AzureOpenAIClientBuilderCustomizer responseTimeoutCustomizer() {
```
return openAiClientBuilder -> {
HttpClientOptions clientOptions = new HttpClientOptions()
.setResponseTimeout(Duration.ofMinutes(5));
openAiClientBuilder.httpClient(HttpClient.createDefault(clientOptions));
Chat Properties
```yaml
6/17
```

| Maven | Gradle |
| --- | --- |
| XML <dependency> <groupId>org.springframework.ai</groupId> <artifactId>spring-ai-starter-model-azure-openai</artifactId> </dependency> |  |

|  | JAVA @Configuration public class AzureOpenAiConfig { @Bean public AzureOpenAIClientBuilderCustomizer responseTimeoutCustomizer() { return openAiClientBuilder -> { HttpClientOptions clientOptions = new HttpClientOptions() .setResponseTimeout(Duration.ofMinutes(5)); openAiClientBuilder.httpClient(HttpClient.createDefault(clientOptions)); }; } } |
| --- | --- |
| Chat P |  |
|  |  |
|  | Chat |

The prefix is the property prefix to configure the connection to Azure OpenAI.
spring.ai.azure.openai
Property Description Default
spring.ai.azure.openai.api-key The Key from Azure AI OpenAI section under -
Keys and Endpoint Resource
Management
spring.ai.azure.openai.endpoint The endpoint from the Azure AI OpenAI section under -
Keys and Endpoint
Resource Management
spring.ai.azure.openai.openai-api-key (non Azure) OpenAI API key. Used to authenticate with the OpenAI service, instead of -
Azure OpenAI. This automatically sets the endpoint to api.openai.com/v1. Use either
api-key or openai-api-key property. With this configuration the
spring.ai.azure.openai.chat.options.deployment-name is treated as an
OpenAi Model name.
spring.ai.azure.openai.custom-headers A map of custom headers to be included in the API requests. Each entry in the map Empty map
represents a header, where the key is the header name and the value is the header
value.
Enabling and disabling of the chat auto-configurations are now configured via top level properties with the prefix spring.ai.model.chat.
To enable, spring.ai.model.chat=azure-openai (It is enabled by default)
To disable, spring.ai.model.chat=none (or any value which doesn’t match azure-openai)
This change is done to allow configuration of multiple models.
The prefix is the property prefix that configures the implementation for Azure OpenAI.
spring.ai.azure.openai.chat ChatModel
```yaml
7/17
```

## Property Description Default

spring.ai.azure.openai.chat.enabled (Removed and no Enable Azure OpenAI chat model. true
longer valid)
spring.ai.model.chat Enable Azure OpenAI chat model. azure-openai
spring.ai.azure.openai.chat.options.deployment-name In use with Azure, this refers to the "Deployment Name" of your model, gpt-4o
which you can find at oai.azure.com/portal. It’s important to note that within
an Azure OpenAI deployment, the "Deployment Name" is distinct from the
model itself. The confusion around these terms stems from the intention to
make the Azure OpenAI client library compatible with the original OpenAI
endpoint. The deployment structures offered by Azure OpenAI and Sam
Altman’s OpenAI differ significantly. Deployments model name to provide
as part of this completions request.
spring.ai.azure.openai.chat.options.maxTokens The maximum number of tokens to generate in the chat completion. The -
total length of input tokens and generated tokens is limited by the model’s
context length. Use for non-reasoning models (e.g., gpt-4o, gpt-3.5-
turbo). Cannot be used with maxCompletionTokens.
spring.ai.azure.openai.chat.options.maxCompletionTokens An upper bound for the number of tokens that can be generated for a com‐ -
pletion, including visible output tokens and reasoning tokens. Required for
reasoning models (e.g., o1, o3, o4-mini series). Cannot be used with
maxTokens.
spring.ai.azure.openai.chat.options.temperature The sampling temperature to use that controls the apparent creativity of 0.7
generated completions. Higher values will make output more random while
lower values will make results more focused and deterministic. It is not rec‐
ommended to modify temperature and top_p for the same completions re‐
quest as the interaction of these two settings is difficult to predict.
spring.ai.azure.openai.chat.options.topP An alternative to sampling with temperature called nucleus sampling. This -
value causes the model to consider the results of tokens with the provided
probability mass.
```yaml
8/17
```

## Property Description Default

spring.ai.azure.openai.chat.options.logitBias A map between GPT token IDs and bias scores that influences the proba‐ -
bility of specific tokens appearing in a completions response. Token IDs
are computed via external tokenizer tools, while bias scores reside in the
range of -100 to 100 with minimum and maximum values corresponding to
a full ban or exclusive selection of a token, respectively. The exact behav‐
ior of a given bias score varies by model.
spring.ai.azure.openai.chat.options.user An identifier for the caller or end user of the operation. This may be used -
for tracking or rate-limiting purposes.
spring.ai.azure.openai.chat.options.stream-usage (For streaming only) Set to add an additional chunk with token usage sta‐ false
tistics for the entire request. The field for this chunk is an empty
choices
array and all other chunks will also include a usage field, but with a null
value.
spring.ai.azure.openai.chat.options.n The number of chat completions choices that should be generated for a -
chat completions response.
spring.ai.azure.openai.chat.options.stop A collection of textual sequences that will end completions generation. -
spring.ai.azure.openai.chat.options.presencePenalty A value that influences the probability of generated tokens appearing -
based on their existing presence in generated text. Positive values will
make tokens less likely to appear when they already exist and increase the
model’s likelihood to output new topics.
spring.ai.azure.openai.chat.options.responseFormat.type Compatible with GPT-4o, mini, and all -
GPT-4o GPT-4 Turbo GPT-
models newer than gpt-3.5-turbo-1106. The
3.5 Turbo
type enables JSON mode, which guarantees the message
JSON_OBJECT
the model generates is valid JSON. The type enables
JSON_SCHEMA
Structured Outputs which guarantees the model will match your supplied
JSON schema. The type requires setting the
JSON_SCHEMA
property as well.
responseFormat.schema
```yaml
9/17
```

|  |  | spring.ai.azure.openai.chat.options.responseFormat.type | Compatible with GPT-4o, GPT-4o mini, GPT-4 Turbo and all GPT- 3.5 Turbo models newer than gpt-3.5-turbo-1106. The JSON_OBJECT type enables JSON mode, which guarantees the message the model generates is valid JSON. The JSON_SCHEMA type enables Structured Outputs which guarantees the model will match your supplied JSON schema. The JSON_SCHEMA type requires setting the responseFormat.schema property as well. | - |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
|  |  |  |  |  |

## Property Description Default

spring.ai.azure.openai.chat.options.responseFormat.schema Response format JSON schema. Applicable only for -
responseFormat.type=JSON_SCHEMA
spring.ai.azure.openai.chat.options.frequencyPenalty A value that influences the probability of generated tokens appearing -
based on their cumulative frequency in generated text. Positive values will
make tokens less likely to appear as their frequency increases and de‐
crease the likelihood of the model repeating the same statements
verbatim.
spring.ai.azure.openai.chat.options.tool-names List of tools, identified by their names, to enable for function calling in a -
single prompt request. Tools with those names must exist in the
ToolCallback registry.
spring.ai.azure.openai.chat.options.tool-callbacks Tool Callbacks to register with the ChatModel. -
spring.ai.azure.openai.chat.options.internal-tool-execution- If false, the Spring AI will not handle the tool calls internally, but will proxy true
enabled them to the client. Then it is the client’s responsibility to handle the tool
calls, dispatch them to the appropriate function, and return the results. If
true (the default), the Spring AI will handle the function calls internally.
Applicable only for chat models with function calling support
All properties prefixed with can be overridden at runtime by adding a request specific Runtime Options to
spring.ai.azure.openai.chat.options
the call.
Prompt
Token Limit Parameters: Model-Specific Usage
Azure OpenAI has model-specific requirements for token limiting parameters:
```yaml
10/17
```

## Model Family Required Parameter Notes

Reasoning Models maxCompletionTokens These models only accept maxCompletionTokens. Using maxTokens will re‐
(o1, o3, o4-mini series)
sult in an API error.
Non-Reasoning Models Traditional models use for output limiting. Using
maxTokens maxTokens
(gpt-4o, gpt-3.5-turbo, etc.) maxCompletionTokens may result in an API error.
The parameters and are mutually exclusive. Setting both parameters simultaneously will result in an API error
maxTokens maxCompletionTokens
from Azure OpenAI. The Spring AI Azure OpenAI client will automatically clear the previously set parameter when you set the other one, with a warning
message.
```yaml
Example: Using maxCompletionTokens for reasoning models
```
var options = AzureOpenAiChatOptions.builder()
.deploymentName("o1-preview")
.maxCompletionTokens(500) // Required for reasoning models
.build();
```yaml
Example: Using maxTokens for non-reasoning models
```
var options = AzureOpenAiChatOptions.builder()
.deploymentName("gpt-4o")
.maxTokens(500) // Required for non-reasoning models
.build();
Runtime Options
The AzureOpenAiChatOptions.java provides model configurations, such as the model to use, the temperature, the frequency penalty, etc.
On start-up, the default options can be configured with the AzureOpenAiChatModel(api, options) constructor or the
properties.
spring.ai.azure.openai.chat.options.*
```yaml
11/17
```
At runtime you can override the default options by adding new, request specific, options to the call. For example to override the de‐
Prompt
fault model and temperature for a specific request:
ChatResponse response = chatModel.call(
new Prompt(
"Generate the names of 5 famous pirates.",
AzureOpenAiChatOptions.builder()
.deploymentName("gpt-4o")
.temperature(0.4)
.build()
In addition to the model specific AzureOpenAiChatOptions.java you can use a portable ChatOptions instance, created with the ChatOptions#builder().
Function Calling
You can register custom Java functions with the AzureOpenAiChatModel and have the model intelligently choose to output a JSON object
containing arguments to call one or many of the registered functions. This is a powerful technique to connect the LLM capabilities with exter‐
nal tools and APIs. Read more about Tool Calling.
Multimodal
Multimodality refers to a model’s ability to simultaneously understand and process information from various sources, including text, images,
audio, and other data formats. Presently, the Azure OpenAI gpt-4o model offers multimodal support.
The Azure OpenAI can incorporate a list of base64-encoded images or image urls with the message. Spring AI’s Message interface facili‐
tates multimodal AI models by introducing the Media type. This type encompasses data and details regarding media attachments in mes‐
sages, utilizing Spring’s org.springframework.util.MimeType and a java.lang.Object for the raw media data.
```yaml
12/17
```
Below is a code example excerpted from OpenAiChatModelIT.java, illustrating the fusion of user text with an image using the
GPT_4_O
model.
URL url = new URL("
String response = ChatClient.create(chatModel).prompt()
.options(AzureOpenAiChatOptions.builder().deploymentName("gpt-4o").build())
.user(u -> u.text("Explain what do you see on this picture?").media(MimeTypeUtils.IMAGE_PNG, this.url))
.call()
.content();
you can pass multiple images as well.
It takes as an input the image:
multimodal.test.png
along with the text message "Explain what do you see on this picture?", and generates a response like this:
This is an image of a fruit bowl with a simple design. The bowl is made of metal with curved wire edges that
create an open structure, allowing the fruit to be visible from all angles. Inside the bowl, there are two
yellow bananas resting on top of what appears to be a red apple. The bananas are slightly overripe, as
indicated by the brown spots on their peels. The bowl has a metal ring at the top, likely to serve as a handle
for carrying. The bowl is placed on a flat surface with a neutral-colored background that provides a clear
view of the fruit inside.
You can also pass in a classpath resource instead of a URL as shown in the example below
```yaml
13/17
```

|  | This is an image of a fruit bowl with a simple design. The bowl is made of metal with curved wire edges that create an open structure, allowing the fruit to be visible from all angles. Inside the bowl, there are two yellow bananas resting on top of what appears to be a red apple. The bananas are slightly overripe, as indicated by the brown spots on their peels. The bowl has a metal ring at the top, likely to serve as a handle for carrying. The bowl is placed on a flat surface with a neutral-colored background that provides a clear view of the fruit inside. |
| --- | --- |
| You can |  |
|  | You ca |

Resource resource = new ClassPathResource("multimodality/multimodal.test.png");
String response = ChatClient.create(chatModel).prompt()
.options(AzureOpenAiChatOptions.builder()
.deploymentName("gpt-4o").build())
.user(u -> u.text("Explain what do you see on this picture?")
.media(MimeTypeUtils.IMAGE_PNG, this.resource))
.call()
.content();
Sample Controller
Create a new Spring Boot project and add the spring-ai-starter-model-azure-openai to your pom (or gradle) dependencies.
Add a application.properties file, under the src/main/resources directory, to enable and configure the OpenAi chat model:
```properties
spring.ai.azure.openai.api-key=YOUR_API_KEY
spring.ai.azure.openai.endpoint=YOUR_ENDPOINT
spring.ai.azure.openai.chat.options.deployment-name=gpt-4o
spring.ai.azure.openai.chat.options.temperature=0.7
```
replace the api-key and endpoint with your Azure OpenAI credentials.
This will create a implementation that you can inject into your class. Here is an example of a simple
AzureOpenAiChatModel
```java
class that uses the chat model for text generations.
@Controller
@RestController
public class ChatController {
private final AzureOpenAiChatModel chatModel;
14/17
```

|  | JAVA @RestController public class ChatController { private final AzureOpenAiChatModel chatModel; |
| --- | --- |
|  | publi p |

```java
@Autowired
public ChatController(AzureOpenAiChatModel chatModel) {
```
this.chatModel = chatModel;
```java
@GetMapping("/ai/generate")
public Map generate(@RequestParam(value = "message", defaultValue = "Tell me a joke") String message) {
```
return Map.of("generation", this.chatModel.call(message));
```java
@GetMapping("/ai/generateStream")
public Flux<ChatResponse> generateStream(@RequestParam(value = "message", defaultValue = "Tell me a joke")
```
String message) {
Prompt prompt = new Prompt(new UserMessage(message));
return this.chatModel.stream(prompt);
Manual Configuration
The AzureOpenAiChatModel implements the ChatModel and StreamingChatModel and uses the Azure OpenAI Java Client.
To enable it, add the spring-ai-azure-openai dependency to your project’s Maven pom.xml file:
```xml
<dependency>
<groupId>org.springframework.ai</groupId>
<artifactId>spring-ai-azure-openai</artifactId>
</dependency>
```
or to your Gradle build file.
build.gradle
```yaml
15/17
```
dependencies {
implementation 'org.springframework.ai:spring-ai-azure-openai'
Refer to the Dependency Management section to add the Spring AI BOM to your build file.
The dependency also provide the access to the AzureOpenAiChatModel. For more information about the
spring-ai-azure-openai
refer to the Azure OpenAI Chat section.
AzureOpenAiChatModel
Next, create an instance and use it to generate text responses:
AzureOpenAiChatModel
var openAIClientBuilder = new OpenAIClientBuilder()
.credential(new AzureKeyCredential(System.getenv("AZURE_OPENAI_API_KEY")))
.endpoint(System.getenv("AZURE_OPENAI_ENDPOINT"));
var openAIChatOptions = AzureOpenAiChatOptions.builder()
.deploymentName("gpt-5")
.temperature(0.4)
.maxCompletionTokens(200)
.build();
var chatModel = AzureOpenAiChatModel.builder()
.openAIClientBuilder(openAIClientBuilder)
.defaultOptions(openAIChatOptions)
.build();
ChatResponse response = chatModel.call(
new Prompt("Generate the names of 5 famous pirates."));
```java
// Or with streaming responses
16/17
```

|  | JAVA var openAIClientBuilder = new OpenAIClientBuilder() .credential(new AzureKeyCredential(System.getenv("AZURE_OPENAI_API_KEY"))) .endpoint(System.getenv("AZURE_OPENAI_ENDPOINT")); var openAIChatOptions = AzureOpenAiChatOptions.builder() .deploymentName("gpt-5") .temperature(0.4) .maxCompletionTokens(200) .build(); var chatModel = AzureOpenAiChatModel.builder() .openAIClientBuilder(openAIClientBuilder) .defaultOptions(openAIChatOptions) .build(); ChatResponse response = chatModel.call( new Prompt("Generate the names of 5 famous pirates.")); // Or with streaming responses |
| --- | --- |
|  | // Or |

Flux<ChatResponse> streamingResponses = chatModel.stream(
new Prompt("Generate the names of 5 famous pirates."));
the gpt-4o is actually the Deployment Name as presented in the Azure AI Portal.
Apache®, Apache Tomcat®, Apache Kafka®, Apache Cassandra™, and Apache Geode™ are trademarks or registered trademarks of the
Apache Software Foundation in the United States and/or other countries. Java™, Java™ SE, Java™ EE, and OpenJDK™ are trademarks of
Oracle and/or its affiliates. Kubernetes® is a registered trademark of the Linux Foundation in the United States and other countries.
Linux® is the registered trademark of Linus Torvalds in the United States and other countries. Windows® and Microsoft® Azure are
registered trademarks of Microsoft Corporation. “AWS” and “Amazon Web Services” are trademarks or registered trademarks of
Amazon.com Inc. or its affiliates. All other trademarks and copyrights are property of their respective owners and are only mentioned
for informative purposes. Other names may be trademarks of their respective owners.
```yaml
17/17
```