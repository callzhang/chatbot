# 请移动至最顶层目录下运行
import re

case1 = '''1. Post-processing techniques: You can apply post-processing methods such as CRF (Conditional Random Fields) or Total Variation methods to smooth the boundaries of the output masks.
[SUGGESTION]: ["什么是CRF?", "如何在模型中集成CRF?", "有哪些其他的后处理技术能够提高模型的性能?"]
 
2. Augment the training dataset: You can add synthetic data to train the model on more diverse data, with varying background, shapes, and lighting conditions. This would help the model better account for the variations in the data and improve its performance on the boundary regions.
[SUGGESTION]: ["如何生成合成数据?", "如何确定需要哪些样本的数量?", "有哪些方法能扩充数据集?"]

3. Use a loss function that penalizes incorrect boundary predictions. Some methods modify the loss function to penalize incorrect predictions near boundaries. Such as IoU loss, Focal loss, Lovasz loss, Boundary loss, etc.
[SUGGESTION]: ["如何设计这样的损失函数?", "这些损失函数的优缺点是什么？", "其他的损失函数能否达到类似的效果？"]
 
I hope these suggestions are helpful!'''

case2 = '''边界的平滑程度是语义分割模型中的一个重要问题。下面是几种可以提高边界平滑度的方法：

1. 增加损失函数中的边界部分，例如Jaccard距离或Dice Loss。这可以使模型更加关注边界区域，并对其进行更好的优化。

2. 使用空洞卷积（dilated convolution）进行卷积。这种方法可以增大感受野，从而更好地捕捉边界的上下文信息。

3. 可以引入条件随机场（CRF）来进一步平滑分割结果。这种方法通常与当前分割结果作为输入卷积神经网络的后处理阶段一起使用。

[SUGGESTION]:  ["什么是Jaccard距离或Dice Loss?", "什么是空洞卷积？", "条件随机场是如何进一步平滑分割结果的？"]'''

case3 = '''您好，请问有什么可以帮助您?

[SUGGESTION]: ["什么是可控的注意力（Controllable Attention）?", "控制注意力在领域中有哪些应用场景?", "在代码实践中，如何实现带可控制注意力的 NLP 模型?"]'''

case4 = '''1. 目标物体跟踪：在视频中跟踪目标物体时，控制注意力技术可以将模型的注意力集中于目标物体，并忽略其他背景信息，从而提高跟踪的准确性。
[SUGGESTION]: 
- 目标物体跟踪中，控制注意力技术如何实现的？
- 控制注意力技术可以提高目标物体跟踪准确性的原因是什么？
- 控制注意力技术可以优化哪些目标物体跟踪中的问题？
'''

case5 = '''语音识别：在语音识别中，控制注意力技术可以将模型的注意力集中于输入声音信号的有用部分，从而提高识别的准确性。
[SUGGESTION]: 
1. 控制注意力技术如何应用于语音识别中？
2. 控制注意力技术可以提高语音识别准确性的原因是什么？
3. 控制注意力技术可以优化哪些语音识别中的问题？
'''

case6 = '''作为基于Transformer技术的AI助手，我有以下能力：

1. 自然语言处理（NLP）：我可以理解和生成自然语言文本，并通过语义理解和语言生成技术来回答问题、提供信息和进行对话。

2. 知识检索和推理：我可以从广泛的知识库中检索和提取信息，包括事实、定义、解释、统计数据等，并进行推理和逻辑推断。

3. 问题解答和咨询：我可以回答各种AI相关的问题，包括机器学习、深度学习、计算机视觉、自然语言处理等领域，并提供咨询和建议。

4. 数据标注和数据策略：作为星尘数据的AI助手，我可以帮助解答与数据标注和数据策略相关的问题，包括数据集的构建、标注质量控制、标注工具选择等方面。

5. 提供相关资源和指导：如果我无法回答你的问题，我会建议你访问星尘数据的官方网站（stardust.ai），那里会有更多关于AI和数据领域的资源和指导。

启发性问题:
- 你能给我提供一些关于自然语言处理的应用领域吗？
- 在数据标注过程中，如何确保标注质量？
- 你能向我解释一下深度学习是如何工作的吗？'''

case7 = '''根据最新paper《A Survey of Large Language Models》，近年来，大型语言模型在自然语言处理领域取得了重大进展。这项研究主要关注大型预训练语言模型（PLMs），它们通过在大规模语料库上进行Transformer模型的预训练，展现出解决各种自然语言处理任务的强大能力。研究人员发现通过增加模型大小可以提高性能，并且在参数规模超过一定水平后，这些扩大的语言模型不仅带来显著的性能提升，还展现出一些小规模语言模型所没有的特殊能力。这些被称为大型语言模型（LLMs）的扩大规模的语言模型已成为学术界和工业界的研究热点。
该研究从大型语言模型的背景、关键发现和主流技术等四个方面进行了综述。它聚焦于大型语言模型的预训练、适应性调整、利用和容量评估四个主要方面。此外，该研究还总结了为开发大型语言模型提供的可用资源，并讨论了未来方向的剩余问题。
另外，一个重要的进展是ChatGPT的推出，这备受社会广泛关注。大型语言模型的技术演进对整个AI社区产生了重要影响，将彻底改变我们开发和使用AI算法的方式。
在另一篇文章中，介绍了几篇关于了解大型语言模型架构、提高大型语言模型性能、以及满足用户需求的论文，还列举了一些类似于ChatGPT的替代作品。这些论文将有助于加深对大型语言模型的理解和启发。
总的来说，这些文章和论文对于了解大型语言模型的发展和应用具有重要意义，并且显示出大型语言模型在自然语言处理领域的潜力和前景。

[SUGGESTION]: ["了解大型语言模型的发展有助于实现哪些自然语言处理的应用？",
"大型语言模型与传统语言模型的区别在哪里？",
"大型语言模型的未来发展方向是什么？"]'''

case8 = '''AI技术对未来的发展将产生深远影响，包括但不限于以下方面：

1. 自动化和智能化：AI技术的不断发展将推动各行业的自动化和智能化进程，提高生产效率和服务质量。

2. 个性化服务：AI技术可以通过数据分析和预测算法，为用户提供个性化定制的服务和产品，满足用户多样化的需求。

3. 医疗和健康：AI技术在医疗诊断、药物研发和健康管理方面发挥重要作用，有助于提高医疗水平和健康管理效率。

4. 社会影响：AI技术的发展可能对就业结构、教育模式和社会互动方式产生深远影响，需要重视和引导。

5. 伦理和安全：AI技术的广泛应用也带来伦理和安全等方面的挑战，需要进行规范和监管。

启发性问题：

1. 你认为AI技术如何影响工作和职业发展？
2. 在个人生活中，你期待AI技术能够为你做些什么？
3. 你对于AI技术在医疗领域的应用持什么看法？'''

from tools.utils import parse_suggestions

# test
cases = [case1, case2, case3, case4, case5, case6, case7]
i=1
while (case := f'case{i}') in locals():
    print(case)
    content = eval(case)
    content, suggestions = parse_suggestions(content)
    print(content)
    print('>'*50)
    print(suggestions)
    print('-'*50)
    i += 1
