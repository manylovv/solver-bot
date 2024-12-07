import 'dotenv/config';

import {
  conversations,
  createConversation,
  type Conversation,
  type ConversationFlavor,
} from '@grammyjs/conversations';
import { spawn } from 'child_process';
import { Bot, Context, InlineKeyboard, session } from 'grammy';
import { dedent } from 'ts-dedent';

type MyContext = Context & ConversationFlavor;
type MyConversation = Conversation<MyContext>;

const bot = new Bot<MyContext>(process.env.BOT_TOKEN!);

bot.use(session({ initial: () => ({}) }));
bot.use(conversations());

const inlineKeyboard = new InlineKeyboard().text(
  'давай решим другое уравнение',
  'solve'
);

const solveEquations = (equations: string[], variables: string) => {
  return new Promise((resolve, reject) => {
    const childProcess = spawn('python3', [
      'solver.py',
      `-i ${JSON.stringify({ equations, variables })}`,
    ]);

    let stdout = '';
    let stderr = '';

    childProcess.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    childProcess.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    childProcess.on('close', (code) => {
      if (code === 0) {
        resolve(stdout);
      } else {
        reject(new Error(stderr || 'Process failed'));
      }
    });
  });
};

async function greeting(conversation: MyConversation, ctx: MyContext) {
  ctx.reply(
    dedent`
      ща все решим, отправляй свое уравнение в таком формате:

      b = a * 0.972 + 20.83 * 0
      c = b * 0.974 + (20.83 - b) * 0.0314
      d = c * 0.979 + (20.83 - b - c) * 0.0353
      e = d * 0.980 + (20.83 - b - c - d) * 0.0285
      f = e * 0.980 + (20.83 - b - c - d - e) * 0.0294
      b + c + d + e + f = 14

      важно! 
      между каждым уравнением должен быть перенос строки
      для десятичных дробей используй точку, а не запятую
      умножение: *
      деление: /
      сложение: +
      вычитание: -

      бот пока ещё глупый и не умеет решать уравнения с переменными в которых есть числа (w1, w2 и т.д.)
      так что замени всё на буквы =)
    `
  );

  const { message } = await conversation.wait();
  if (!message || !message.text) return;

  const trimmedMessage = message.text.trim();
  const equations = trimmedMessage.split('\n');

  await ctx.reply(
    dedent`
      супер, теперь присылай переменные, которые надо найти, через запятую:

      a, b, c, d, e, f
    `
  );

  const { message: variablesMessage } = await conversation.wait();

  if (!variablesMessage || !variablesMessage.text) return;

  const variables = variablesMessage.text
    .trim()
    .split(',')
    .map((variable) => variable.trim());

  try {
    const result = await solveEquations(equations, variables.join(','));

    await ctx.reply(result as string, {
      reply_markup: inlineKeyboard,
    });
  } catch (error) {
    await ctx.reply(
      dedent`
        что-то пошло не так 😭
        проверь, что ты правильно ввел уравнения и переменные
      `,
      {
        reply_markup: inlineKeyboard,
      }
    );
  }
}

bot.use(createConversation(greeting));

bot.command('start', async (ctx) => {
  await ctx.conversation.enter('greeting');
});

bot.callbackQuery('solve', async (ctx) => {
  await ctx.conversation.enter('greeting');
});

bot.start();
