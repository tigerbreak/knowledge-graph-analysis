#include "../include/sparkchain.h"
#include "../include/sc_llm.h"

#include <iostream>
#include <string>
#include <atomic>
#include <Windows.h>
#include <regex>

#define GREEN "\033[32m"
#define YELLOW "\033[33m"
#define RED "\033[31m"
#define RESET "\033[0m"

using namespace SparkChain;
using namespace std;

// async status tag
static atomic_bool finish(false);
// result cache
string final_result = "";


class SparkCallbacks : public LLMCallbacks {
	void onLLMResult(LLMResult* result, void* usrContext) {
		int status = result->getStatus();
		printf(GREEN "%d:%s:%s " "usrContext:%d\n" RESET, status, result->getRole(), result->getContent(), *(int*)usrContext);
		final_result += string(result->getContent());
		if (status == 2) {
			printf(GREEN "tokens:%d + %d = %d "  "usrContext:%d\n" RESET, result->getCompletionTokens(), result->getPromptTokens(), result->getTotalTokens(), *(int*)usrContext);
			finish = true;
		}
	}
	void onLLMEvent(LLMEvent* event, void* usrContext) {
		printf(YELLOW "onLLMEventCB\n  eventID:%d eventMsg:%s "  "usrContext:%d\n" RESET, event->getEventID(), event->getEventMsg(), *(int*)usrContext);
	}
	void onLLMError(LLMError* error, void* usrContext) {
		printf(RED "onLLMErrorCB\n errCode:%d errMsg:%s "  "usrContext:%d\n" RESET, error->getErrCode(), error->getErrMsg(), *(int*)usrContext);
		finish = true;
	}
};

int initSDK()
{
	// 全局初始化
	SparkChainConfig *config = SparkChainConfig::builder();
	config->appID("")        // 你的appid
		->apiSecret("") // 你的apisecret
		->apiKey("");        // 你的apikey
	int ret = SparkChain::init(config);
	printf(RED "\ninit SparkChain result:%d" RESET, ret);
	return ret;
}

void syncLLMTest()
{
	cout << "\n######### 同步调用 #########" << endl;
	// 配置大模型参数
	LLMConfig *llmConfig = LLMConfig::builder();
	llmConfig->domain("4.0Ultra");
	llmConfig->url("ws(s)://spark-api.xf-yun.com/v4.0/chat");

	Memory* window_memory = Memory::WindowMemory(5);
	LLM *syncllm = LLM::create(llmConfig, window_memory);

	// Memory* token_memory = Memory::TokenMemory(500);
	// LLM *syncllm = LLM::create(llmConfig,token_memory);

	int i = 0;
	const char* input = "你好用英语怎么说？";
	while (i++ < 2)
	{
		// 同步请求
		LLMSyncOutput *result = syncllm->run(input);
		if (result->getErrCode() != 0)
		{
			printf(RED "\nsyncOutput: %d:%s\n\n" RESET, result->getErrCode(), result->getErrMsg());
			continue;
		}
		else
		{
			printf(GREEN "\nsyncOutput: %s:%s\n" RESET, result->getRole(), result->getContent());
		}
		input = "那日语呢？";
	}
	// 垃圾回收
	if (syncllm != nullptr)
	{
		LLM::destroy(syncllm);
	}
}

void asyncLLMTest()
{
	cout << "\n######### 异步调用 #########" << endl;
	// 配置大模型参数
	LLMConfig *llmConfig = LLMConfig::builder();
	llmConfig->domain("4.0Ultra");
	llmConfig ->url("ws(s)://spark-api.xf-yun.com/v4.0/chat");
	Memory* window_memory = Memory::WindowMemory(5);
	LLM *asyncllm = LLM::create(llmConfig, window_memory);

	// Memory* token_memory = Memory::TokenMemory(500);
	// LLM *asyncllm = LLM::create(llmConfig,token_memory);
	if (asyncllm == nullptr)
	{
		printf(RED "\nLLMTest fail, please setLLMConfig before" RESET);
		return;
	}
	// 注册监听回调
	SparkCallbacks *cbs = new SparkCallbacks();
	asyncllm->registerLLMCallbacks(cbs);

	// 异步请求
	int i = 0;
	const char* input = "你好用英语怎么说？";
	while (i++ < 2)
	{
		finish = false;
		int usrContext = 1;
		int ret = asyncllm->arun(input, &usrContext);
		if (ret != 0)
		{
			printf(RED "\narun failed: %d\n\n" RESET, ret);
			finish = true;
			continue;
		}

		int times = 0;
		while (!finish)
		{ // 等待结果返回退出
			Sleep(1000);
			if (times++ > 10) // 等待十秒如果没有最终结果返回退出
				break;
		}
		input = "那日语呢？";
	}
	// 垃圾回收
	if (asyncllm != nullptr)
	{
		LLM::destroy(asyncllm);
	}
	if (cbs != nullptr)
		delete cbs;
}

void uninitSDK()
{
	// 全局逆初始化
	SparkChain::unInit();
}

int main(int argc, char const *argv[])
{
	system("chcp 65001");
	cout << "\n######### llm Demo #########" << endl;
	// 全局初始化
	int ret = initSDK();
	if (ret != 0)
	{
		cout << "initSDK failed:" << ret << endl;
		return -1;
	}

	// 同步调用和异步调用选择一个执行
	syncLLMTest(); // 同步调用

	 asyncLLMTest(); // 异步调用

	// 退出
	uninitSDK();
}
