# Open-Meteo 许可证与条款摘录

摘录时间：2026-11-11（Asia/Shanghai，UTC+8）。只摘与今晚使用相关的段落，不代替原文。官方许可证页 `https://open-meteo.com/en/license` 今晚用 WebFetch / curl 取到的 HTML 几乎无正文（页面很可能依赖脚本渲染），因此**数据许可证措辞以项目 README 的 Data License 节为准**；托管 API 的使用限制以 Terms of Use 页为准。

## 1. 数据许可证（CC BY 4.0）

来源：`https://raw.githubusercontent.com/open-meteo/open-meteo/main/README.md`（2026-11-11，HTTP 200）。相关原文：

> Open-Meteo is an open-source weather API that offers free access for non-commercial use. No API key is required, so you can start using it immediately.

> - Free for non-commercial use with data under Attribution 4.0 International (CC BY 4.0)

> ## Data License
>
> API data is offered under the Attribution 4.0 International license (CC BY 4.0).
>
> You are free to share: copy and redistribute the material in any medium or format and adapt: remix, transform, and build upon the material.
>
> Attribution: You must give appropriate credit, provide a link to the license, and indicate whether changes were made. You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use.
>
> Include an attribution link next to any location where Open-Meteo data is displayed, for example:
>
> `<a href="https://open-meteo.com/">Weather data by Open-Meteo.com</a>`

同文件还写明：软件源码为 GNU Affero General Public License Version 3（AGPLv3）或后续版本。今晚只下载 API 返回的 CSV，不托管其服务端代码；若以后自建 Open-Meteo 服务，需单独阅读 AGPL。

CC BY 4.0 许可证文本：`https://creativecommons.org/licenses/by/4.0/`

## 2. 托管免费 API 的使用条件（与数据许可证不同层）

来源：`https://open-meteo.com/en/terms`（2026-11-11，HTTP 200，从 HTML 抽取可见文本）。Features 页 `https://open-meteo.com/en/features` 同时写明：非商业使用无需 SDK 或鉴权。

Terms 中与 Free API、非商业使用相关的段落（HTML 去标签后的连续文本，排版可能与页面不完全一致）：

> Non-Commercial Use By using the Free API for non-commercial use you agree to following terms: Less than 10'000 API calls per day, 5'000 per hour and 600 per minute. You may only use the free API services for non-commercial purposes. You accept to the CC-BY 4.0 licence, as specified in the licence conditions. We reserve the right to block applications and IP addresses that misuse our service without prior notice. Rate limits are applied by IP addresses and application. [...] Non-commercial use is defined as elaborated by creative commons. To make it easier to understand, here are some examples that qualify as non-commercial use: Private or non-profit websites or apps that do not have subscriptions or advertising. Personal home automation purposes. Public research conducted at public institutions. Use in educational content. Voluntary donations, including contributions through a tip jar, are permitted. On the other hand, the following examples are considered commercial use: Websites or apps that have subscriptions or display advertisements. Commercial products or promotional activities. Undisclosed research at commercial entities. If you plan to use our service for commercial purposes or require additional API calls, we kindly request you to consider subscribing to our API plans [...]

教育用途、公立机构公开研究被其举例为非商业，与课程/毕设原型较吻合。若以后做商业产品或超过速率限制，应改用付费托管或自建，而不是继续按免费档假设。

## 3. 空气质量与历史气象的数据来源归属（须一并写出）

空气质量文档 `https://open-meteo.com/en/docs/air-quality-api`（2026-11-11，HTTP 200）可见：

> Forecast is based on the 11 kilometre CAMS European air quality forecast and the 45 kilometre CAMS global atmospheric composition forecasts. The European and global domain are not coupled and may show different forecasts.

> CAMS European air quality forecasts, ENSEMBLE data. Copernicus Atmosphere Monitoring Service (CAMS) Atmosphere Data Store (ADS). [...] All users of Open-Meteo data must provide a clear attribution to CAMS ENSEMBLE data provider as well as a reference to Open-Meteo.

该页表格还列出 CAMS European Air Quality Forecast / Reanalysis（欧洲，0.1°，约 11 km）与 CAMS Global Atmospheric Composition Forecasts（全球，0.4°，约 45 km）。兰州不在欧洲域。今晚下载的空气质量 CSV 元数据未给出 domain 字段。

历史气象文档 `https://open-meteo.com/en/docs/historical-weather-api`（2026-11-11，HTTP 200）可见：

> Gap-free and consistent historical weather data using weather reanalysis from ERA5 (0.25°, from 1940) and ERA5-Land (0.1°, from 1950) and ECMWF IFS (9 km, from 2017).

> Generated using Copernicus Climate Change Service information 2022.

今晚的 Archive 请求未指定 `models`，CSV 未写模式名称。

## 4. 今晚下载的样品如何署名（建议句）

图或表旁可同时写：Weather data by Open-Meteo.com（CC BY 4.0）；空气质量源数据来自 Copernicus Atmosphere Monitoring Service（CAMS）；历史气象使用 Open-Meteo Historical Weather / Archive API（文档称结合 ERA5 / ERA5-Land / ECMWF IFS 等）。并注明请求点为兰州市区参考坐标，接口实际返回点见 `samples/样本说明.md`，以及下载日期 2026-11-11。
