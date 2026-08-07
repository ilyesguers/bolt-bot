//
//  ModMenu.m — قالب عميل المود مينو لـ eFootball (المباريات الآفلانية فقط)
//
//  هذا قالب توضيحي: يقرأ إعدادات لوحة التحكم من
//      http://<PROXY_IP>:<PORT>/api/modmenu/config
//  ويطبّق المفاتيح محلياً داخل اللعبة. أسماء الدوال الحقيقية للعبة
//  تُكتشف بفك الـ IPA — اربطها مكان أسطر TODO أدناه.
//
//  البناء: theos (انظر docs/OFFLINE_MOD_MENU.md)
//  الاستخدام: شغّل اللعبة المعدّلة والبروكسي مضبوط على الواي فاي.
//
#import <Foundation/Foundation.h>

// --- الإعدادات -----------------------------------------------------------
static NSString *const kConfigURL = @"http://192.168.1.100:8080/api/modmenu/config";
static const NSTimeInterval kPollInterval = 4.0;

// --- قراءة الإعدادات (خيط خلفي) ------------------------------------------
static NSDictionary *FetchModConfig(void) {
    NSURL *url = [NSURL URLWithString:kConfigURL];
    NSMutableURLRequest *req = [NSMutableURLRequest requestWithURL:url];
    req.timeoutInterval = 3.0;
    NSURLResponse *response = nil;
    NSError *error = nil;
    NSData *data = [NSURLConnection sendSynchronousRequest:req
                                         returningResponse:&response
                                                     error:&error];
    if (error || !data) return nil;
    NSDictionary *json = [NSJSONSerialization JSONObjectWithData:data
                                                        options:0
                                                          error:nil];
    if (![json isKindOfClass:[NSDictionary class]]) return nil;
    return json[@"features"];   // {"instant_finish": true, ...}
}

static BOOL IsEnabled(NSDictionary *features, NSString *key) {
    return [features[key] boolValue];
}

// --- مثال التطبيق: اربط دوال اللعبة الحقيقية هنا --------------------------
// بعد فك الـ IPA ستعرف أسماء الدوال، مثلاً:
//   - دالة تنهي المباراة وتعود بالنتيجة
//   - دالة تحسب ذكاء الخصم (لتأخيرها أو إضعاف دقتها)
//   - دالة حساب الستامينا (لإيقاف نقصانها)

static void ApplyInstantFinish(void) {
    // TODO: استدعِ دالة إنهاء المباراة في اللعبة:
    //   [GameMatchController finishMatchWithScore:3:0];
    NSLog(@"[ModMenu] instant_finish -> finishMatch");
}

static void ApplyAutoWin(void) {
    // TODO: اكتب النتيجة في ذاكرة اللعبة:
    //   *(int *)scoreAddress = 3;  *(int *)(scoreAddress + 4) = 0;
    NSLog(@"[ModMenu] auto_win -> set score 3-0");
}

static void ApplySlowAI(void) {
    // TODO: اخفض سرعة/ذكاء الخصم:
    //   *(float *)aiReactionTimeAddress = 0.1f;
    NSLog(@"[ModMenu] slow_ai_client -> ai reaction slowed");
}

static void ApplyAIMiss(void) {
    // TODO: أضعف دقة تسديد الخصم:
    //   *(float *)aiShotAccuracyAddress = 0.0f;
    NSLog(@"[ModMenu] ai_miss_client -> ai shots off target");
}

static void ApplyStamina(void) {
    // TODO: أوقف نقصان الستامينا:
    //   *(BOOL *)staminaDrainEnabledAddress = NO;
    NSLog(@"[ModMenu] stamina_client -> stamina drain off");
}

static void ApplyStatsMax(void) {
    // TODO: ارفع تقييمات الفريق محلياً:
    //   for (player in myTeam) player.rating = 99;
    NSLog(@"[ModMenu] stats_max_client -> players 99");
}

// --- الحلقة الرئيسية ------------------------------------------------------
static void *ModMenuLoop(void *unused) {
    @autoreleasepool {
        while (true) {
            NSDictionary *features = FetchModConfig();
            if (features) {
                if (IsEnabled(features, @"instant_finish"))   ApplyInstantFinish();
                if (IsEnabled(features, @"auto_win"))         ApplyAutoWin();
                if (IsEnabled(features, @"slow_ai_client"))   ApplySlowAI();
                if (IsEnabled(features, @"ai_miss_client"))   ApplyAIMiss();
                if (IsEnabled(features, @"stamina_client"))   ApplyStamina();
                if (IsEnabled(features, @"stats_max_client")) ApplyStatsMax();
            }
            usleep((useconds_t)(kPollInterval * 1000000.0));
        }
    }
    return NULL;
}

// --- نقطة الدخول (يستدعيها الـ dylib عند التحميل) --------------------------
__attribute__((constructor))
static void ModMenuEntry(void) {
    pthread_t thread;
    pthread_create(&thread, NULL, ModMenuLoop, NULL);
    NSLog(@"[ModMenu] loaded — polling %@", kConfigURL);
}
