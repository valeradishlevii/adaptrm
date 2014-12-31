def get_activity_data(user, date_from, date_to, scheme):
        field_dict = {'id': 'id', 'name': 'name', 'appName': 'app_name', 'appDetails': 'app_details', 'task': 'task__name',
                      'duration': 'duration', 'confidence': 'project_confidence', 'clientName': 'project__client__name',
                      'projectName': 'project__name', 'projectId': 'project_id', 'deviceId': 'device_id'}
        if scheme == 'timeline':
            field_dict.update({
                'fromDate': 'start',
                'toDate': 'end',
                'device': 'device__name'
            })
        elif scheme == 'categorization':
            field_dict.update({
                'domain': 'domain'
            })
        activities = Activity.objects.filter(user=user, start__range=(date_from, date_to)).\
            values(*field_dict.values())
        result_dict = {'data': []}
        time_start = time.time()
        for activity in activities:
            api_obj = {}
            for api_name, db_name in field_dict.items():
                if type(activity[db_name]) == datetime:
                    activity[db_name] = activity[db_name].astimezone(pytz.utc).strftime("%s")
                elif type(activity[db_name]) == Decimal:
                    activity[db_name] = str(activity[db_name])
                api_obj[api_name] = activity[db_name] if not activity[db_name] == 'n/a' else ""
            result_dict['data'].append(api_obj)
        return result_dict

def with_superuser_rights(fn):
    "Check user have passed firewall, authenticated and marked as superuser"
    def __to_superuser_only(request, *args, **kwds):
        if not Firewall.allowed(request, True):
            return Firewall.show(request, True)
        if not request.user.is_authenticated() or not request.user.is_superuser:
            return redirect('/')
        return fn(request, *args, **kwds)
    return __to_superuser_only


class featuresets_redirect(object):
    def __init__(self, location, *args):
        self.location = location
        self.fs_codes = args
        
    def __call__(self, f):
        def wrapped_f(request, *args, **kwargs):
            if request.user.is_authenticated():
                is_active = AccountUtils.is_fs_set_active(request.user, self.fs_codes)
                if is_active:
                    resp = f(request, *args, **kwargs)
                    return resp
                else:
                    return redirect(self.location)
            else:
                return redirect(self.location)
        return wrapped_f


def check_gae_cron(func):
    @wraps(func)
    def wrapper(request, args=None):
        if request.META['REMOTE_ADDR'] != '0.1.0.1' or not request.META.get('HTTP_X_APPENGINE_CRON', False) == 'true':
            logging.info("Cron task forbidden. Meta info: %s" % request.META)
            return HttpResponseForbidden()
        return func(request, args)
    return wrapper
