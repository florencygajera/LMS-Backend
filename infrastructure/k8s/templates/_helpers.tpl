{{- define "agniveer.name" -}}
agniveer-sentinel
{{- end -}}

{{- define "agniveer.fullname" -}}
{{- printf "%s-%s" (include "agniveer.name" .) .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
