FROM alpine as builder

RUN apk add --no-cache postgresql

FROM alpine

RUN apk add --no-cache libpq
COPY --from=builder /usr/bin/pgbench /usr/bin/pgbench

CMD ["pgbench"]