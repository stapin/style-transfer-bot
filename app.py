import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.types import Message, BufferedInputFile, FSInputFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
import os
from concurrent.futures import ProcessPoolExecutor

logging.basicConfig(level=logging.INFO, filename="app-logs.log")

from model import get_transferd_img

task_queue = asyncio.Queue()
job_done = dict()
save_path = os.getcwd() + "/tmp"



bot = Bot(token=os.getenv("TG_BOT_TOKEN"))
dp = Dispatcher()

kb = [ [types.KeyboardButton(text="Transfer image style")] ]
keyboard = types.ReplyKeyboardMarkup(
    keyboard=kb,
    resize_keyboard=True
)

class StyleTransferRequest(StatesGroup):
    upload_content_img = State()
    upload_style_img = State()
    wait_img = State()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Hello! This is a style transfer bot. Send a content image and a style image, when bot will generate you" +
                         " photo with content from the content photo and style from the style photo.", 
                         reply_markup=keyboard)


@dp.message(StateFilter(None), F.text.lower() == "transfer image style")
async def transfer_style(message: Message, state: FSMContext):
    await message.answer("Send content photo", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(StyleTransferRequest.upload_content_img)

    

@dp.message(StateFilter(StyleTransferRequest.upload_content_img), F.photo)
async def download_content_photo(message: Message, bot: Bot, state: FSMContext):
    if (not os.path.exists(save_path + f"/{message.from_user.id}")):
        os.makedirs(save_path + f"/{message.from_user.id}")
    await bot.download(
        message.photo[-1],
        destination=save_path + f"/{message.from_user.id}/content.jpg"
    )
    await message.answer("Send style photo")
    await state.set_state(StyleTransferRequest.upload_style_img)


@dp.message(StateFilter(StyleTransferRequest.upload_style_img), F.photo)
async def download_style_photo(message: Message, bot: Bot, state: FSMContext):
    await bot.download(
        message.photo[-1],
        destination=save_path + f"/{message.from_user.id}/style.jpg"
    )
    await message.answer("Wait for a result. It may take a long time.")
    job_done[message.from_user.id] = False
    await task_queue.put(message.from_user.id)
    await wait_for_job(message.from_user.id)
    await message.answer_photo(FSInputFile(save_path + f"/{message.from_user.id}/result.jpg"), 
                               reply_markup=keyboard)
    await state.set_state(None)
    await delete_files(message.from_user.id)

async def wait_for_job(id):
    while not job_done[id]:
        await asyncio.sleep(2)

async def delete_files(id):
    path = save_path + f"/{id}/"
    os.remove(path + "content.jpg")
    os.remove(path + "result.jpg")
    os.remove(path + "style.jpg")

async def execute_task_queue():
    with ProcessPoolExecutor() as executor:
        loop = asyncio.get_event_loop()
        while True:
            if (not task_queue.empty()):
                user_id = await task_queue.get()
                await loop.run_in_executor(executor, get_transferd_img, user_id)
                job_done[user_id] = True
            else:
                await asyncio.sleep(2)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(execute_task_queue())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())



