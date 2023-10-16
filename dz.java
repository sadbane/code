package org.example;

import org.openqa.selenium.JavascriptExecutor;
import java.time.Duration;
import org.openqa.selenium.By;
import java.util.List;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.Keys;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.util.HashMap;
import java.util.Map;


public class App {

    public static void main(String[] args) {

        // путь до драйвера
        System.setProperty("webdriver.chrome.driver", "C:\\driver\\chromedriver.exe");
        // Создаем HashMap для хранения элементов до сортировки
        Map<String, WebElement> elementsBeforeSort = new HashMap<>();

        // экземпляр создали
        WebDriver driver = new ChromeDriver();

        try {
            // Открыл браузер на весь экран
            driver.manage().window().maximize();

            // Перешёл на yandex.ru
            driver.get("https://www.market.yandex.ru/");

            // нашёл элемент каталог и кликнул по нему
            WebElement catalogLink = driver.findElement(By.xpath("//span[contains(text(),'Каталог')]"));
            //нажал на элемент каталог
            catalogLink.click();

            // Вэбдрайвервайт использовал для ожидания открытия окна, сначала юзал
            // Thread.sleep , потом прочитал что это так себе для автотестов
            WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(2));

            //ExpectedConditions.elementToBeClickable - выполняет условия пока элемент не станет кликабельным
            WebElement smartphonesLink = wait.until(ExpectedConditions.elementToBeClickable(By.xpath("//a[@class='egKyN _1mqvV _1wg9X' and contains(text(),'Смартфоны')]")));
            Thread.sleep(5000);
            // нажал на элемент смартфоны
            smartphonesLink.click();
            // нажал и кликнул на элемент все фильтры

            WebElement allFilters = wait.until(ExpectedConditions.elementToBeClickable(By.xpath("//span[contains(text(),'Все фильтры')]")));
            Thread.sleep(1000);
            allFilters.click();

            // вводим макс прайс
            WebElement maxPriceInput = wait.until(ExpectedConditions.elementToBeClickable(By.xpath("//input[@data-auto='range-filter-input-max']")));
            maxPriceInput.sendKeys("20000");

            // выбираем диагональ от 3 дюйма
            WebElement diagonalelementekran = wait.until(ExpectedConditions.elementToBeClickable(By.xpath("//button[@aria-controls='14805766']")));
            JavascriptExecutor js = (JavascriptExecutor) driver;
            js.executeScript("arguments[0].scrollIntoView(true);", diagonalelementekran);
            diagonalelementekran.click();

            // вводим диагональ 3
            // Найти поле ввода для диагонали
            WebElement diagonalelementinput = driver.findElement(By.xpath("//body/div[3]/section[1]/div[2]/div[1]/div[1]/div[2]/div[1]/div[19]/div[1]/div[1]/div[1]/div[1]/input[1]"));
            diagonalelementinput.sendKeys("3");


            // выбираем популярных
            WebElement appleLink = wait.until(ExpectedConditions.elementToBeClickable(By.xpath("//label[@id='153043']")));
            WebElement honorLink = wait.until(ExpectedConditions.elementToBeClickable(By.xpath("//label[@id='459710']")));
            WebElement huaweiLink = wait.until(ExpectedConditions.elementToBeClickable(By.xpath("//label[@id='153061']")));
            WebElement samsungLink = wait.until(ExpectedConditions.elementToBeClickable(By.xpath("//label[@id='7701962']")));
            WebElement xiaomiLink = wait.until(ExpectedConditions.elementToBeClickable(By.xpath("//label[@id='15292504']")));
            // кликаем популярных
            appleLink.click();
            Thread.sleep(1000);
            honorLink.click();
            Thread.sleep(1000);
            huaweiLink.click();
            Thread.sleep(1000);
            samsungLink.click();
            Thread.sleep(1000);
            xiaomiLink.click();


            // здесь сделал по класс нейму элемент "показать % предложений(я)"
            WebElement showOffersLink = driver.findElement(By.xpath("//a[contains(@class, '_2qvOO') and contains(@class, '_3qN-v') and contains(@class, '_1Rc6L')]"));
            Thread.sleep(1000);
            // кликнули на элемент "Показать % предложений(я)"
            showOffersLink.click();


            // if (phoneNames.size() == 10) {
              //  System.out.println("Список состоит из 10 элементов.");
            //} else {
              //  System.out.println("Список НЕ состоит из 10 элементов.");
            //}
            


        } catch (InterruptedException e) {
            e.printStackTrace();

        } finally {
            // Закрыть браузер и завершить работу с WebDriver
            driver.quit();
        }
    }
    private static String getElementId(WebElement element) {
        return element.getAttribute("id");
    }
}
